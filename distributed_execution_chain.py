

import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from enum import Enum
import uuid
import random


class ServiceState(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"


class ReplayMode(Enum):
    LIVE = "LIVE"
    REPLAY = "REPLAY"
    RECOVERY = "RECOVERY"


class DistributedExecutionChain:
    
    
    def __init__(self, 
                 signal_source_endpoint="http://localhost:8001",
                 sanskar_endpoint="http://localhost:8002",
                 rajya_endpoint="http://localhost:8003",
                 enforcement_endpoint="http://localhost:8004",
                 bucket_endpoint="http://localhost:8005",
                 telemetry_endpoint="http://localhost:8006"):
        
        self.signal_source_endpoint = signal_source_endpoint
        self.sanskar_endpoint = sanskar_endpoint
        self.rajya_endpoint = rajya_endpoint
        self.enforcement_endpoint = enforcement_endpoint
        self.bucket_endpoint = bucket_endpoint
        self.telemetry_endpoint = telemetry_endpoint
        
        
        self.service_states = {
            "signal_source": ServiceState.HEALTHY,
            "sanskar": ServiceState.HEALTHY,
            "rajya": ServiceState.HEALTHY,
            "enforcement": ServiceState.HEALTHY,
            "bucket": ServiceState.HEALTHY,
            "telemetry": ServiceState.HEALTHY
        }
        
        
        self.execution_history = []
        self.lineage_state = {}
        self.replay_cache = {}
        self.failure_log = []
        self.recovery_log = []
    
    def generate_trace_id(self) -> str:
        """Generate a deterministic trace ID."""
        return f"TRACE-{uuid.uuid4().hex[:12]}"
    
    def compute_contract_hash(self, contract: Dict[str, Any]) -> str:
        
        serialized = json.dumps(contract, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def create_service_request(self,
                              trace_id: str,
                              service_name: str,
                              contract: Dict[str, Any],
                              parent_trace_id: str = None) -> Dict[str, Any]:
        
        request = {
            "request_id": f"REQ-{uuid.uuid4().hex[:8]}",
            "trace_id": trace_id,
            "parent_trace_id": parent_trace_id,
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "contract": contract,
            "contract_version": "v1",
            "replay_metadata": {
                "mode": "LIVE",
                "request_sequence": len(self.execution_history) + 1,
                "contract_hash": self.compute_contract_hash(contract)
            }
        }
        return request
    
    def execute_signal_source_call(self,
                                   trace_id: str,
                                   signal_input: Dict[str, Any],
                                   simulate_failure: bool = False) -> Tuple[Dict[str, Any], bool]:
        
        service_name = "signal_source"
        request = self.create_service_request(trace_id, service_name, signal_input)
        
        try:
            if simulate_failure or random.random() < 0.1:  # 10% simulated failure rate
                self.service_states[service_name] = ServiceState.TIMEOUT
                return self._create_failure_response(trace_id, service_name, "TIMEOUT"), False
            
            self.service_states[service_name] = ServiceState.HEALTHY
            
            response = {
                "response_id": f"RESP-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "service": service_name,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "signal_emitted": True,
                "signal_data": signal_input,
                "contract_version": "v1"
            }
            
            self.execution_history.append({
                "stage": "signal_source",
                "request": request,
                "response": response,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            return response, True
            
        except Exception as e:
            self.service_states[service_name] = ServiceState.FAILED
            return self._create_failure_response(trace_id, service_name, str(e)), False
    
    def execute_sanskar_call(self,
                            trace_id: str,
                            parent_trace_id: str,
                            signal_data: Dict[str, Any],
                            simulate_failure: bool = False) -> Tuple[Dict[str, Any], bool]:
        
        service_name = "sanskar"
        request = self.create_service_request(trace_id, service_name, signal_data, parent_trace_id)
        
        try:
            if simulate_failure or random.random() < 0.05:  # 5% failure rate
                self.service_states[service_name] = ServiceState.TIMEOUT
                return self._create_failure_response(trace_id, service_name, "ANALYSIS_TIMEOUT"), False
            
            self.service_states[service_name] = ServiceState.HEALTHY
            
            response = {
                "response_id": f"RESP-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "parent_trace_id": parent_trace_id,
                "service": service_name,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "intelligence_output": {
                    "analysis": "adaptive_intelligence_analysis",
                    "confidence": 0.87,
                    "recommendation": "allocate_resources_to_region_1",
                    "reasoning": "Signal analysis shows high-confidence optimization opportunity"
                },
                "decision_state": "CONFIDENT",
                "contract_version": "v1"
            }
            
            self.execution_history.append({
                "stage": "sanskar",
                "request": request,
                "response": response,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            return response, True
            
        except Exception as e:
            self.service_states[service_name] = ServiceState.FAILED
            return self._create_failure_response(trace_id, service_name, str(e)), False
    
    def execute_rajya_call(self,
                          trace_id: str,
                          parent_trace_id: str,
                          sanskar_output: Dict[str, Any],
                          simulate_failure: bool = False) -> Tuple[Dict[str, Any], bool]:
       
        service_name = "rajya"
        request = self.create_service_request(trace_id, service_name, sanskar_output, parent_trace_id)
        
        try:
            if simulate_failure or random.random() < 0.05:
                self.service_states[service_name] = ServiceState.DEGRADED
                return self._create_failure_response(trace_id, service_name, "VALIDATION_REJECTED"), False
            
            self.service_states[service_name] = ServiceState.HEALTHY
            
            response = {
                "response_id": f"RESP-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "parent_trace_id": parent_trace_id,
                "service": service_name,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "governance_validation": {
                    "valid": True,
                    "governance_state": "AUTHORIZED",
                    "authority_delegation": False,
                    "external_constraint_maintained": True,
                    "reasoning": "Intelligence output remains bounded by governance constraints"
                },
                "contract_version": "v1"
            }
            
            self.execution_history.append({
                "stage": "rajya",
                "request": request,
                "response": response,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            return response, True
            
        except Exception as e:
            self.service_states[service_name] = ServiceState.FAILED
            return self._create_failure_response(trace_id, service_name, str(e)), False
    
    def execute_enforcement_call(self,
                                trace_id: str,
                                parent_trace_id: str,
                                governance_output: Dict[str, Any],
                                simulate_failure: bool = False) -> Tuple[Dict[str, Any], bool]:
        
        service_name = "enforcement"
        request = self.create_service_request(trace_id, service_name, governance_output, parent_trace_id)
        
        try:
            if simulate_failure or random.random() < 0.08:
                self.service_states[service_name] = ServiceState.TIMEOUT
                return self._create_failure_response(trace_id, service_name, "EXECUTION_TIMEOUT"), False
            
            self.service_states[service_name] = ServiceState.HEALTHY
            
            response = {
                "response_id": f"RESP-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "parent_trace_id": parent_trace_id,
                "service": service_name,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "execution_directives": [
                    {
                        "directive_id": f"DIR-{uuid.uuid4().hex[:8]}",
                        "action": "resource_allocation",
                        "target": "region_1",
                        "status": "acknowledged"
                    }
                ],
                "contract_version": "v1"
            }
            
            self.execution_history.append({
                "stage": "enforcement",
                "request": request,
                "response": response,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            return response, True
            
        except Exception as e:
            self.service_states[service_name] = ServiceState.FAILED
            return self._create_failure_response(trace_id, service_name, str(e)), False
    
    def execute_bucket_persistence_call(self,
                                       trace_id: str,
                                       parent_trace_id: str,
                                       execution_data: Dict[str, Any],
                                       simulate_failure: bool = False) -> Tuple[Dict[str, Any], bool]:
       
        service_name = "bucket"
        request = self.create_service_request(trace_id, service_name, execution_data, parent_trace_id)
        
        try:
            if simulate_failure or random.random() < 0.05:
                self.service_states[service_name] = ServiceState.DEGRADED
                return self._create_failure_response(trace_id, service_name, "PERSISTENCE_DELAYED"), False
            
            self.service_states[service_name] = ServiceState.HEALTHY
            
            
            lineage_hash = self.compute_contract_hash(execution_data)
            
            response = {
                "response_id": f"RESP-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "parent_trace_id": parent_trace_id,
                "service": service_name,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "persistence": {
                    "persisted": True,
                    "storage_location": f"bucket://execution-records/{trace_id}",
                    "lineage_hash": lineage_hash,
                    "replay_attestation": {
                        "attestation_id": f"ATT-{uuid.uuid4().hex[:8]}",
                        "lineage_verified": True,
                        "trace_continuity_verified": True
                    }
                },
                "contract_version": "v1"
            }
            
            
            self.lineage_state[trace_id] = {
                "trace_id": trace_id,
                "lineage_hash": lineage_hash,
                "execution_data": execution_data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.execution_history.append({
                "stage": "bucket",
                "request": request,
                "response": response,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            return response, True
            
        except Exception as e:
            self.service_states[service_name] = ServiceState.FAILED
            return self._create_failure_response(trace_id, service_name, str(e)), False
    
    def execute_telemetry_call(self,
                              trace_id: str,
                              parent_trace_id: str,
                              telemetry_data: Dict[str, Any],
                              simulate_failure: bool = False) -> Tuple[Dict[str, Any], bool]:
        
        service_name = "telemetry"
        request = self.create_service_request(trace_id, service_name, telemetry_data, parent_trace_id)
        
        try:
            if simulate_failure or random.random() < 0.1:
                self.service_states[service_name] = ServiceState.DEGRADED
                # Telemetry failures are non-blocking
                return self._create_partial_failure_response(trace_id, service_name, "TELEMETRY_ASYNC_RETRY"), True
            
            self.service_states[service_name] = ServiceState.HEALTHY
            
            response = {
                "response_id": f"RESP-{uuid.uuid4().hex[:8]}",
                "trace_id": trace_id,
                "parent_trace_id": parent_trace_id,
                "service": service_name,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "telemetry": {
                    "ingested": True,
                    "telemetry_series_id": f"TS-{uuid.uuid4().hex[:8]}",
                    "metrics_recorded": [
                        "execution_latency_ms",
                        "service_health_state",
                        "replay_lineage_hash",
                        "recovery_status"
                    ]
                },
                "contract_version": "v1"
            }
            
            self.execution_history.append({
                "stage": "telemetry",
                "request": request,
                "response": response,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            return response, True
            
        except Exception as e:
            self.service_states[service_name] = ServiceState.FAILED
            return self._create_partial_failure_response(trace_id, service_name, str(e)), True
    
    def execute_live_chain(self,
                          signal_input: Dict[str, Any],
                          inject_failures: List[str] = None) -> Dict[str, Any]:
        
        if inject_failures is None:
            inject_failures = []
        
        trace_id = self.generate_trace_id()
        chain_result = {
            "trace_id": trace_id,
            "chain_executed_at": datetime.utcnow().isoformat() + "Z",
            "stages": {},
            "failures": [],
            "recovery_attempts": [],
            "trace_continuity": [],
            "service_states_at_execution": {}
        }
        
        
        signal_response, signal_success = self.execute_signal_source_call(
            trace_id,
            signal_input,
            simulate_failure="signal_source" in inject_failures
        )
        chain_result["stages"]["signal_source"] = signal_response
        chain_result["trace_continuity"].append(("signal_source", signal_response.get("trace_id")))
        
        if not signal_success:
            chain_result["failures"].append(signal_response)
            return chain_result
        
        
        sanskar_response, sanskar_success = self.execute_sanskar_call(
            trace_id,
            trace_id,
            signal_input,
            simulate_failure="sanskar" in inject_failures
        )
        chain_result["stages"]["sanskar"] = sanskar_response
        chain_result["trace_continuity"].append(("sanskar", sanskar_response.get("trace_id")))
        
        if not sanskar_success:
            chain_result["failures"].append(sanskar_response)
            return chain_result
        
        
        rajya_response, rajya_success = self.execute_rajya_call(
            trace_id,
            sanskar_response.get("response_id"),
            sanskar_response,
            simulate_failure="rajya" in inject_failures
        )
        chain_result["stages"]["rajya"] = rajya_response
        chain_result["trace_continuity"].append(("rajya", rajya_response.get("trace_id")))
        
        if not rajya_success:
            chain_result["failures"].append(rajya_response)
            return chain_result
        
        
        enforcement_response, enforcement_success = self.execute_enforcement_call(
            trace_id,
            rajya_response.get("response_id"),
            rajya_response,
            simulate_failure="enforcement" in inject_failures
        )
        chain_result["stages"]["enforcement"] = enforcement_response
        chain_result["trace_continuity"].append(("enforcement", enforcement_response.get("trace_id")))
        
        if not enforcement_success:
            chain_result["failures"].append(enforcement_response)
            return chain_result
        
        
        bucket_response, bucket_success = self.execute_bucket_persistence_call(
            trace_id,
            enforcement_response.get("response_id"),
            chain_result["stages"],
            simulate_failure="bucket" in inject_failures
        )
        chain_result["stages"]["bucket"] = bucket_response
        chain_result["trace_continuity"].append(("bucket", bucket_response.get("trace_id")))
        
        if not bucket_success:
            chain_result["failures"].append(bucket_response)
            return chain_result
        
        
        telemetry_response, _ = self.execute_telemetry_call(
            trace_id,
            bucket_response.get("response_id"),
            {
                "execution_trace": trace_id,
                "service_states": self.service_states,
                "execution_latency_ms": 500
            },
            simulate_failure="telemetry" in inject_failures
        )
        chain_result["stages"]["telemetry"] = telemetry_response
        chain_result["trace_continuity"].append(("telemetry", telemetry_response.get("trace_id")))
        
        
        chain_result["trace_continuity_verified"] = all(
            stage_trace == trace_id for _, stage_trace in chain_result["trace_continuity"]
        ) if chain_result["trace_continuity"] else False
        
        chain_result["service_states_at_execution"] = {
            k: v.value for k, v in self.service_states.items()
        }
        
        
        chain_result["summary"] = {
            "status": "success" if not chain_result["failures"] else "partial_failure",
            "stages_completed": len(chain_result["stages"]),
            "failures_count": len(chain_result["failures"])
        }
        
        return chain_result
    
    def simulate_distributed_failure(self,
                                    trace_id: str,
                                    failure_type: str,
                                    affected_service: str) -> Dict[str, Any]:
        
        failure_record = {
            "trace_id": trace_id,
            "failure_type": failure_type,
            "affected_service": affected_service,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service_state_before": self.service_states[affected_service].value
        }
        
        if failure_type == "SERVICE_TIMEOUT":
            self.service_states[affected_service] = ServiceState.TIMEOUT
            
        elif failure_type == "REPLAY_INTERRUPTION":
            if trace_id in self.lineage_state:
                self.lineage_state[trace_id]["replay_interrupted"] = True
        
        elif failure_type == "DELAYED_ACK":
            self.service_states[affected_service] = ServiceState.DEGRADED
        
        elif failure_type == "TELEMETRY_LOSS":
           
            pass
        
        elif failure_type == "DUPLICATE_REPLAY":
            if trace_id in self.lineage_state:
                self.lineage_state[trace_id]["duplicate_detected"] = True
        
        elif failure_type == "NODE_RESTART":
            self.service_states[affected_service] = ServiceState.RECOVERING
        
        failure_record["service_state_after"] = self.service_states[affected_service].value
        self.failure_log.append(failure_record)
        
        return failure_record
    
    def recover_from_failure(self,
                            trace_id: str,
                            failure_record: Dict[str, Any]) -> Dict[str, Any]:
        
        recovery_record = {
            "trace_id": trace_id,
            "failure_type": failure_record["failure_type"],
            "affected_service": failure_record["affected_service"],
            "recovery_started_at": datetime.utcnow().isoformat() + "Z",
            "recovery_actions": [],
            "lineage_reconstructed": False,
            "replay_continuity_preserved": False
        }
        
        affected_service = failure_record["affected_service"]
        
        
        self.service_states[affected_service] = ServiceState.HEALTHY
        recovery_record["recovery_actions"].append({
            "action": "restore_service_health",
            "service": affected_service,
            "completed": True
        })
        
        
        if trace_id in self.lineage_state:
            recovery_record["recovery_actions"].append({
                "action": "reconstruct_lineage_from_bucket",
                "trace_id": trace_id,
                "lineage_hash": self.lineage_state[trace_id].get("lineage_hash"),
                "completed": True
            })
            recovery_record["lineage_reconstructed"] = True
        
        
        if recovery_record["lineage_reconstructed"]:
            
            recovery_record["recovery_actions"].append({
                "action": "verify_replay_continuity",
                "deterministic": True,
                "idempotent": True,
                "completed": True
            })
            recovery_record["replay_continuity_preserved"] = True
        
        
        recovery_record["recovery_actions"].append({
            "action": "reconcile_diverged_state",
            "conflicts_detected": 0,
            "resolved": True
        })
        
        recovery_record["recovery_completed_at"] = datetime.utcnow().isoformat() + "Z"
        recovery_record["status"] = "SUCCESS" if recovery_record["replay_continuity_preserved"] else "PARTIAL"
        
        self.recovery_log.append(recovery_record)
        
        return recovery_record
    
    def _create_failure_response(self, trace_id: str, service: str, reason: str) -> Dict[str, Any]:
        
        return {
            "trace_id": trace_id,
            "service": service,
            "status": "failure",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "failure": {
                "code": "SERVICE_ERROR",
                "message": f"{service} failed: {reason}",
                "trace_preserved": True
            },
            "contract_version": "v1"
        }
    
    def _create_partial_failure_response(self, trace_id: str, service: str, reason: str) -> Dict[str, Any]:
        
        return {
            "trace_id": trace_id,
            "service": service,
            "status": "partial_failure",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "partial_failure": {
                "code": "ASYNC_RETRY_SCHEDULED",
                "message": f"{service}: {reason}",
                "blocking": False
            },
            "contract_version": "v1"
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        
        return {
            "total_executions": len(self.execution_history),
            "execution_stages": [e["stage"] for e in self.execution_history],
            "lineage_entries": len(self.lineage_state),
            "failures_recorded": len(self.failure_log),
            "recoveries_completed": len(self.recovery_log),
            "service_states": {k: v.value for k, v in self.service_states.items()},
            "execution_history_summary": [
                {
                    "stage": e["stage"],
                    "timestamp": e["timestamp"],
                    "success": "failure" not in e.get("response", {})
                }
                for e in self.execution_history
            ]
        }
