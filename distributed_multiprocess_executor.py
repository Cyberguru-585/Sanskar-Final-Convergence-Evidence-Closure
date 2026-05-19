

import json
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

import uuid
import time
import hashlib
import subprocess
import os
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import threading
from dataclasses import dataclass, asdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockRedisClient:
    
    
    def __init__(self):
        self.data = {}
    
    def lpush(self, key: str, value: str):
        if key not in self.data:
            self.data[key] = []
        self.data[key].insert(0, value)
    
    def brpop(self, key: str, timeout: int = 5):
        if key in self.data and self.data[key]:
            return (key, self.data[key].pop())
        return None
    
    def delete(self, key: str):
        if key in self.data:
            del self.data[key]
    
    def ping(self):
        return True


class ServiceRole(Enum):
    SIGNAL_SOURCE = "signal_source"
    SANSKAR = "sanskar"
    CORE = "core"
    ENFORCEMENT = "enforcement"
    TRUTH = "truth"
    OBSERVABILITY = "observability"


class ProcessState(Enum):
    INITIALIZING = "INITIALIZING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    RECOVERING = "RECOVERING"
    DEAD = "DEAD"


class ReplayMode(Enum):
    LIVE = "LIVE"
    REPLAY = "REPLAY"
    RECOVERY = "RECOVERY"


@dataclass
class ServiceMessage:
    
    message_id: str
    trace_id: str
    source_service: str
    target_service: str
    payload: Dict[str, Any]
    timestamp: str
    replay_mode: str = "LIVE"
    sequence_number: int = 0
    content_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceMessage':
        return cls(**data)


@dataclass
class ProcessRecord:
    
    process_id: str
    service_role: str
    process_handle: Optional[int] = None
    state: str = "INITIALIZING"
    health_status: str = "INITIALIZING"
    last_heartbeat: str = ""
    restart_count: int = 0
    messages_processed: int = 0
    failures: List[str] = None
    
    def __post_init__(self):
        if self.failures is None:
            self.failures = []


class DistributedMultiProcessExecutor:
    
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None
        self.process_registry: Dict[str, ProcessRecord] = {}
        self.message_history: List[ServiceMessage] = []
        self.recovery_log: List[Dict[str, Any]] = []
        self.trace_map: Dict[str, List[str]] = {}  # trace_id -> list of service visits
        self.failure_injection_enabled = False
        self.failure_scenarios: List[Dict[str, Any]] = []
        
    def connect_redis(self) -> bool:
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis module not available - using in-memory queue simulation")
            self.redis_client = MockRedisClient()
            return True
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e} - using mock")
            self.redis_client = MockRedisClient()
            return True
    
    def register_service_process(self, 
                                service_role: str,
                                process_handle: int) -> ProcessRecord:
        
        process_id = f"PROC-{uuid.uuid4().hex[:8]}"
        record = ProcessRecord(
            process_id=process_id,
            service_role=service_role,
            process_handle=process_handle,
            state="INITIALIZING",
            last_heartbeat=datetime.utcnow().isoformat() + "Z"
        )
        self.process_registry[process_id] = record
        logger.info(f"Registered {service_role} process: {process_id} (PID: {process_handle})")
        return record
    
    def publish_message(self, message: ServiceMessage) -> bool:
        
        if not self.redis_client:
            logger.error("Redis client not connected")
            return False
        
        try:
            
            content = json.dumps(message.payload, sort_keys=True, default=str)
            message.content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            
            queue_key = f"queue:{message.target_service}"
            self.redis_client.lpush(queue_key, json.dumps(message.to_dict()))
            
            
            self.message_history.append(message)
            
            
            if message.trace_id not in self.trace_map:
                self.trace_map[message.trace_id] = []
            self.trace_map[message.trace_id].append(message.source_service)
            
            logger.info(f"Published message from {message.source_service} to {message.target_service} (trace: {message.trace_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def consume_message(self, service_role: str, timeout: int = 5) -> Optional[ServiceMessage]:
        
        if not self.redis_client:
            logger.error("Redis client not connected")
            return None
        
        try:
            queue_key = f"queue:{service_role}"
            result = self.redis_client.brpop(queue_key, timeout=timeout)
            if result:
                _, message_json = result
                message_dict = json.loads(message_json)
                message = ServiceMessage.from_dict(message_dict)
                logger.info(f"Service {service_role} consumed message (trace: {message.trace_id})")
                return message
            return None
        except Exception as e:
            logger.error(f"Failed to consume message for {service_role}: {e}")
            return None
    
    def record_heartbeat(self, process_id: str, state: str = "HEALTHY") -> bool:
        
        if process_id in self.process_registry:
            record = self.process_registry[process_id]
            record.last_heartbeat = datetime.utcnow().isoformat() + "Z"
            record.state = state
            record.health_status = state
            return True
        return False
    
    def check_service_health(self, process_id: str, max_heartbeat_age_seconds: int = 10) -> str:
        
        if process_id not in self.process_registry:
            return "UNKNOWN"
        
        record = self.process_registry[process_id]
        last_heartbeat = datetime.fromisoformat(record.last_heartbeat.replace("Z", "+00:00"))
        age = (datetime.utcnow() - last_heartbeat.replace(tzinfo=None)).total_seconds()
        
        if age > max_heartbeat_age_seconds:
            record.state = "UNHEALTHY"
            record.health_status = "UNHEALTHY"
            return "UNHEALTHY"
        
        return record.state
    
    def inject_failure(self, process_id: str, failure_type: str) -> bool:
        
        if process_id not in self.process_registry:
            logger.error(f"Process {process_id} not found")
            return False
        
        record = self.process_registry[process_id]
        scenario = {
            "process_id": process_id,
            "service_role": record.service_role,
            "failure_type": failure_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "injected": True
        }
        self.failure_scenarios.append(scenario)
        record.state = "DEGRADED"
        record.failures.append(failure_type)
        
        logger.warning(f"Injected failure '{failure_type}' into {record.service_role} (process: {process_id})")
        return True
    
    def simulate_recovery(self, process_id: str) -> bool:
        
        if process_id not in self.process_registry:
            return False
        
        record = self.process_registry[process_id]
        record.state = "RECOVERING"
        record.restart_count += 1
        
        recovery_event = {
            "process_id": process_id,
            "service_role": record.service_role,
            "restart_count": record.restart_count,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "previous_state": "DEGRADED",
            "new_state": "HEALTHY"
        }
        self.recovery_log.append(recovery_event)
        
        record.state = "HEALTHY"
        record.last_heartbeat = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Recovered {record.service_role} after failure (restart #{record.restart_count})")
        return True
    
    def create_trace_id(self) -> str:
        
        return f"TRACE-{uuid.uuid4().hex[:12]}"
    
    def compute_service_contract_hash(self, contract: Dict[str, Any]) -> str:
        
        serialized = json.dumps(contract, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def get_trace_lineage(self, trace_id: str) -> List[str]:
        
        return self.trace_map.get(trace_id, [])
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """Get full process status."""
        if process_id not in self.process_registry:
            return {}
        
        record = self.process_registry[process_id]
        return {
            "process_id": process_id,
            "service_role": record.service_role,
            "state": record.state,
            "health_status": record.health_status,
            "last_heartbeat": record.last_heartbeat,
            "restart_count": record.restart_count,
            "messages_processed": record.messages_processed,
            "failure_count": len(record.failures),
            "failures": record.failures
        }
    
    def get_all_process_status(self) -> Dict[str, Dict[str, Any]]:
        
        return {
            pid: self.get_process_status(pid)
            for pid in self.process_registry.keys()
        }
    
    def get_recovery_history(self) -> List[Dict[str, Any]]:
        
        return self.recovery_log
    
    def get_message_history(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        
        messages = [msg.to_dict() for msg in self.message_history]
        if trace_id:
            messages = [msg for msg in messages if msg["trace_id"] == trace_id]
        return messages
    
    def clear_queues(self) -> bool:
        """Clear all message queues."""
        if not self.redis_client:
            return False
        
        try:
            for role in ServiceRole:
                queue_key = f"queue:{role.value}"
                self.redis_client.delete(queue_key)
            logger.info("Cleared all message queues")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queues: {e}")
            return False
    
    def export_state(self) -> Dict[str, Any]:
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "processes": self.get_all_process_status(),
            "message_count": len(self.message_history),
            "recovery_events": len(self.recovery_log),
            "trace_lineages": self.trace_map,
            "failure_scenarios": self.failure_scenarios,
            "recovery_log": self.recovery_log
        }
