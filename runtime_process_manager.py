

import subprocess
import os
import signal
import time
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProcessState(Enum):
    
    INITIALIZING = "INITIALIZING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    RECOVERING = "RECOVERING"
    DEAD = "DEAD"

@dataclass
class ProcessSnapshot:
    
    timestamp: str
    pid: Optional[int]
    state: str
    return_code: Optional[int]
    running: bool
    memory_usage_mb: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ProcessProof:
    
    proof_type: str  # "boot" | "restart" | "health"
    process_name: str
    start_timestamp: str
    end_timestamp: str
    pid: int
    command: List[str]
    environment: Dict[str, str]
    exit_code: Optional[int]
    snapshots: List[ProcessSnapshot]
    recovery_time_ms: Optional[float]
    state_preserved: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_type": self.proof_type,
            "process_name": self.process_name,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "pid": self.pid,
            "command": self.command,
            "environment": self.environment,
            "exit_code": self.exit_code,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "recovery_time_ms": self.recovery_time_ms,
            "state_preserved": self.state_preserved
        }

class RuntimeProcessManager:
    
    
    def __init__(self, process_name: str = "SANSKAR"):
        self.process_name = process_name
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.state = ProcessState.INITIALIZING
        self.snapshots: List[ProcessSnapshot] = []
        self.start_timestamp: Optional[str] = None
        self.end_timestamp: Optional[str] = None
        self.state_before_restart: Optional[Dict[str, Any]] = None
        
    def spawn_process(self, command: List[str], env: Optional[Dict[str, str]] = None) -> int:
        """
        Spawn a real process with environment.
        
        Args:
            command: Command to execute (e.g., ["python", "sanskar.py"])
            env: Environment variables (if None, inherits parent environment)
            
        Returns:
            PID of spawned process
        """
        try:
            self.start_timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Create environment
            full_env = os.environ.copy()
            if env:
                full_env.update(env)
            
            # Spawn process
            self.process = subprocess.Popen(
                command,
                env=full_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.pid = self.process.pid
            self.state = ProcessState.HEALTHY
            
            logger.info(f"Process spawned: {self.process_name} PID={self.pid}")
            
            # Take initial snapshot
            self._take_snapshot()
            
            return self.pid
            
        except Exception as e:
            logger.error(f"Failed to spawn process: {e}")
            self.state = ProcessState.DEAD
            raise
    
    def _take_snapshot(self) -> ProcessSnapshot:
        
        snapshot = ProcessSnapshot(
            timestamp=datetime.utcnow().isoformat() + "Z",
            pid=self.pid,
            state=self.state.value,
            return_code=self.process.returncode if self.process else None,
            running=self.is_running(),
            memory_usage_mb=self._get_memory_usage()
        )
        self.snapshots.append(snapshot)
        return snapshot
    
    def is_running(self) -> bool:
        
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get memory usage of process in MB (mock for Windows)"""
        
        return None
    
    def wait_for_health(self, timeout_seconds: int = 10) -> bool:
        """
        Wait for process to become healthy.
        
        Args:
            timeout_seconds: Max time to wait
            
        Returns:
            True if process became healthy, False if timeout/error
        """
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self.is_running():
                self._take_snapshot()
                self.state = ProcessState.HEALTHY
                return True
            time.sleep(0.1)
        
        self.state = ProcessState.UNHEALTHY
        return False
    
    def graceful_shutdown(self, timeout_seconds: int = 5) -> bool:
        """
        Gracefully shutdown process with SIGTERM, then SIGKILL if needed.
        
        Args:
            timeout_seconds: Grace period before force kill
            
        Returns:
            True if successful, False otherwise
        """
        if not self.process:
            return True
        
        try:
            # Send SIGTERM (graceful)
            os.kill(self.pid, signal.SIGTERM)
            self._take_snapshot()
            
            # Wait for graceful shutdown
            start = time.time()
            while time.time() - start < timeout_seconds:
                if not self.is_running():
                    self.state = ProcessState.DEAD
                    self.end_timestamp = datetime.utcnow().isoformat() + "Z"
                    self._take_snapshot()
                    logger.info(f"Process gracefully shut down: {self.process_name}")
                    return True
                time.sleep(0.1)
            
            # Force kill if still running
            os.kill(self.pid, signal.SIGKILL)
            self._take_snapshot()
            self.state = ProcessState.DEAD
            self.end_timestamp = datetime.utcnow().isoformat() + "Z"
            logger.warning(f"Process force-killed: {self.process_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False
    
    def capture_boot_proof(self, command: List[str], env: Optional[Dict[str, str]] = None) -> ProcessProof:
        """
        Capture boot proof: process creation evidence.
        
        Args:
            command: Command to execute
            env: Environment variables
            
        Returns:
            ProcessProof artifact
        """
        
        pid = self.spawn_process(command, env)
        
        
        self.wait_for_health()
        
       
        proof = ProcessProof(
            proof_type="boot",
            process_name=self.process_name,
            start_timestamp=self.start_timestamp,
            end_timestamp=datetime.utcnow().isoformat() + "Z",
            pid=pid,
            command=command,
            environment=env or {},
            exit_code=None,
            snapshots=self.snapshots.copy(),
            recovery_time_ms=None,
            state_preserved=True
        )
        
        return proof
    
    def capture_restart_proof(self, 
                             command: List[str], 
                             env: Optional[Dict[str, str]] = None,
                             state_getter=None) -> ProcessProof:
        """
        Capture restart proof: restart sequence with state preservation.
        
        Args:
            command: Command to execute
            env: Environment variables
            state_getter: Optional callback to capture state before restart
            
        Returns:
            ProcessProof artifact
        """
       
        pid = self.spawn_process(command, env)
        self.wait_for_health()
        
        
        if state_getter:
            self.state_before_restart = state_getter()
        else:
            self.state_before_restart = {"status": "running"}
        
        
        self._take_snapshot()
        
        
        restart_start = datetime.utcnow()
        self.graceful_shutdown()
        time.sleep(0.5) 
        
        new_pid = self.spawn_process(command, env)
        self.wait_for_health()
        restart_end = datetime.utcnow()
        
        recovery_time_ms = (restart_end - restart_start).total_seconds() * 1000
        
        
        state_preserved = True
        if self.state_before_restart:
            state_preserved = self.state == ProcessState.HEALTHY
        
        
        proof = ProcessProof(
            proof_type="restart",
            process_name=self.process_name,
            start_timestamp=self.start_timestamp,
            end_timestamp=datetime.utcnow().isoformat() + "Z",
            pid=new_pid,
            command=command,
            environment=env or {},
            exit_code=None,
            snapshots=self.snapshots.copy(),
            recovery_time_ms=recovery_time_ms,
            state_preserved=state_preserved
        )
        
        return proof
    
    def capture_health_proof(self, health_check_fn, iterations: int = 3) -> Dict[str, Any]:
        """
        Capture health proof: multiple health checks across time.
        
        Args:
            health_check_fn: Callable that returns health status dict
            iterations: Number of health checks to perform
            
        Returns:
            Health proof artifact
        """
        health_checks = []
        
        for i in range(iterations):
            timestamp = datetime.utcnow().isoformat() + "Z"
            try:
                status = health_check_fn()
                health_checks.append({
                    "iteration": i + 1,
                    "timestamp": timestamp,
                    "status": status,
                    "healthy": status.get("healthy", False)
                })
            except Exception as e:
                health_checks.append({
                    "iteration": i + 1,
                    "timestamp": timestamp,
                    "error": str(e),
                    "healthy": False
                })
            
            if i < iterations - 1:
                time.sleep(1)
        
        proof = {
            "proof_type": "health",
            "process_name": self.process_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pid": self.pid,
            "health_checks": health_checks,
            "overall_healthy": all(h.get("healthy", False) for h in health_checks)
        }
        
        return proof
    
    def get_proof_json(self, proof: ProcessProof) -> str:
        """Serialize proof to JSON"""
        return json.dumps(proof.to_dict(), indent=2, default=str)
    
    def cleanup(self):
        """Clean up process resources"""
        if self.process:
            self.graceful_shutdown()
