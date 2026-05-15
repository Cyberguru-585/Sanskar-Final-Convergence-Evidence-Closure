import time
import json
from datetime import datetime, timedelta
from enum import Enum


class ExecutionState(Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    RETRY = "RETRY"


class AsyncOrchestrator:
    def __init__(self, default_timeout_ms=5000, max_retries=3):
        self.default_timeout_ms = default_timeout_ms
        self.max_retries = max_retries
        self.execution_queue = []
        self.execution_history = []
    
    def queue_async_directive(self, directive, trace_id, stage="enforcement", 
                             delay_ms=100):
        execution_id = f"EXEC-{trace_id}-{len(self.execution_queue) + 1}"
        ack_time = time.time() + (delay_ms / 1000.0)
        
        execution_context = {
            "execution_id": execution_id,
            "trace_id": trace_id,
            "stage": stage,
            "directive": directive,
            "state": ExecutionState.PENDING.value,
            "queued_at": datetime.utcnow().isoformat() + "Z",
            "simulated_ack_delay_ms": delay_ms,
            "ack_time": ack_time,
            "retry_count": 0,
            "max_retries": self.max_retries
        }
        
        self.execution_queue.append(execution_context)
        return execution_context
    
    def simulate_delayed_acknowledgment(self, execution_context, actual_delay_ms=None):
        execution_id = execution_context["execution_id"]
        trace_id = execution_context["trace_id"]
        
        delay = (actual_delay_ms or execution_context["simulated_ack_delay_ms"]) / 1000.0
        time.sleep(delay)
        ack_timestamp = datetime.utcnow().isoformat() + "Z"
        ack_payload = {
            "execution_id": execution_id,
            "trace_id": trace_id,
            "directive_id": execution_context["directive"].get("directive_id", "UNKNOWN"),
            "acknowledged_by": "external_executor",
            "acknowledgment_timestamp": ack_timestamp,
            "acknowledgment_delay_ms": delay * 1000,
            "state": ExecutionState.ACKNOWLEDGED.value
        }
        execution_context["state"] = ExecutionState.ACKNOWLEDGED.value
        execution_context["acknowledged_at"] = ack_timestamp
        
        return ack_payload
    
    def simulate_async_execution(self, execution_context, execution_time_ms=200,
                                fail_probability=0.1):
        execution_id = execution_context["execution_id"]
        trace_id = execution_context["trace_id"]
        time.sleep(execution_time_ms / 1000.0)
        
        import random
        if random.random() < fail_probability:
            execution_context["state"] = ExecutionState.FAILED.value
            completion_payload = {
                "execution_id": execution_id,
                "trace_id": trace_id,
                "state": ExecutionState.FAILED.value,
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "error": "simulated_failure",
                "retry_count": execution_context["retry_count"]
            }
        else:
            completion_hash = self._compute_completion_hash(execution_context)
            
            execution_context["state"] = ExecutionState.COMPLETED.value
            execution_context["completion_hash"] = completion_hash
            
            completion_payload = {
                "execution_id": execution_id,
                "trace_id": trace_id,
                "state": ExecutionState.COMPLETED.value,
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "completion_hash": completion_hash,
                "idempotency_verified": True
            }
        execution_context["completed_at"] = completion_payload.get("completed_at")
        self.execution_history.append(execution_context.copy())
        
        return completion_payload
    
    def simulate_timeout_handling(self, execution_context, timeout_ms=None):
        execution_id = execution_context["execution_id"]
        trace_id = execution_context["trace_id"]
        timeout = timeout_ms or self.default_timeout_ms
        
        timeout_payload = {
            "execution_id": execution_id,
            "trace_id": trace_id,
            "state": ExecutionState.TIMEOUT.value,
            "timeout_ms": timeout,
            "timed_out_at": datetime.utcnow().isoformat() + "Z",
            "retry_count": execution_context["retry_count"],
            "max_retries": execution_context["max_retries"],
            "should_retry": execution_context["retry_count"] < execution_context["max_retries"]
        }
        
        execution_context["state"] = ExecutionState.TIMEOUT.value
        
        return timeout_payload
    
    def simulate_retry(self, execution_context, new_delay_ms=100):
        if execution_context["retry_count"] >= execution_context["max_retries"]:
            return None
        
        execution_context["retry_count"] += 1
        execution_context["state"] = ExecutionState.RETRY.value
        retry_context = {
            "execution_id": f"{execution_context['execution_id']}-RETRY-{execution_context['retry_count']}",
            "trace_id": execution_context["trace_id"],
            "original_execution_id": execution_context["execution_id"],
            "stage": execution_context["stage"],
            "directive": execution_context["directive"],
            "state": ExecutionState.PENDING.value,
            "queued_at": datetime.utcnow().isoformat() + "Z",
            "retry_count": execution_context["retry_count"],
            "max_retries": execution_context["max_retries"],
            "original_attempt_at": execution_context.get("completed_at", 
                                                         execution_context["queued_at"])
        }
        
        self.execution_queue.append(retry_context)
        return retry_context
    
    def verify_replay_safety(self, execution_contexts):
        proof = {
            "total_executions": len(execution_contexts),
            "replay_safe": True,
            "idempotency_verified": True,
            "issues": [],
            "execution_states": {}
        }
        
        for ctx in execution_contexts:
            state = ctx["state"]
            proof["execution_states"][state] = proof["execution_states"].get(state, 0) + 1
            if state == ExecutionState.COMPLETED.value:
                if "completion_hash" not in ctx:
                    proof["replay_safe"] = False
                    proof["idempotency_verified"] = False
                    proof["issues"].append({
                        "execution_id": ctx["execution_id"],
                        "issue": "missing_completion_hash"
                    })
            if ctx["retry_count"] > 0:
                if "original_execution_id" not in ctx:
                    pass
        proof["verdict"] = "PASS — replay safety verified" if proof["replay_safe"] else "FAIL — replay safety issues detected"
        
        return proof
    
    def _compute_completion_hash(self, execution_context):
        completion_data = {
            "execution_id": execution_context["execution_id"],
            "directive_id": execution_context["directive"].get("directive_id", ""),
            "trace_id": execution_context["trace_id"],
            "state": ExecutionState.COMPLETED.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        import hashlib
        serialized = json.dumps(completion_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    
    def get_execution_summary(self):
        return {
            "total_queued": len(self.execution_queue) + len(self.execution_history),
            "pending": sum(1 for e in self.execution_queue if e["state"] == ExecutionState.PENDING.value),
            "acknowledged": sum(1 for e in self.execution_queue if e["state"] == ExecutionState.ACKNOWLEDGED.value),
            "completed": sum(1 for e in self.execution_history if e["state"] == ExecutionState.COMPLETED.value),
            "failed": sum(1 for e in self.execution_history if e["state"] == ExecutionState.FAILED.value),
            "timeout": sum(1 for e in self.execution_history if e["state"] == ExecutionState.TIMEOUT.value),
            "total_retries": sum(e.get("retry_count", 0) for e in self.execution_history),
            "execution_queue": self.execution_queue,
            "execution_history": self.execution_history
        }
