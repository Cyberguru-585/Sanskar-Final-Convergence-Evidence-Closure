import json
import time
from datetime import datetime
from pathlib import Path
import uuid


class ObservabilityTracker:
    
    
    def __init__(self, log_file="observability.log"):
        self.log_file = log_file
        self.logs = []
        self._load_existing_logs()
        self.correlation_context = {}
    
    def _load_existing_logs(self):
        
        if Path(self.log_file).exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            self.logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    
    def set_correlation_context(self, trace_id, parent_trace_id=None, correlation_id=None):
        
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        self.correlation_context[trace_id] = {
            "trace_id": trace_id,
            "parent_trace_id": parent_trace_id,
            "correlation_id": correlation_id,
            "established_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return self.correlation_context[trace_id]
    
    def get_correlation_context(self, trace_id):
        
        return self.correlation_context.get(trace_id, {
            "trace_id": trace_id,
            "correlation_id": str(uuid.uuid4()),
            "parent_trace_id": None
        })
    
    def record_stage_entry(self, trace_id, stage, contract_version="v1", replay_mode=False):
        
        entry_time = time.time()
        correlation = self.get_correlation_context(trace_id)
        
        return {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "parent_trace_id": correlation.get("parent_trace_id"),
            "stage": stage,
            "event": "stage_entry",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "contract_version": contract_version,
            "replay_mode": replay_mode,
            "entry_time": entry_time
        }
    
    def record_stage_exit(self, trace_id, stage, entry_time, decision_state=None, 
                         success=True, contract_version="v1", replay_mode=False,
                         dependency_status="healthy"):
        
        exit_time = time.time()
        latency_ms = round((exit_time - entry_time) * 1000, 2)
        correlation = self.get_correlation_context(trace_id)
        
        log_entry = {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "parent_trace_id": correlation.get("parent_trace_id"),
            "stage": stage,
            "event": "stage_exit",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "latency_ms": latency_ms,
            "contract_version": contract_version,
            "replay_mode": replay_mode,
            "decision_state": decision_state,
            "success": success,
            "dependency_status": dependency_status
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def record_decision(self, trace_id, stage, decision_state, confidence, score,
                       contract_version="v1", replay_mode=False):
        
        correlation = self.get_correlation_context(trace_id)
        
        log_entry = {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "parent_trace_id": correlation.get("parent_trace_id"),
            "stage": stage,
            "event": "decision_point",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision_state": decision_state,
            "confidence": confidence,
            "score": score,
            "contract_version": contract_version,
            "replay_mode": replay_mode
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def record_error(self, trace_id, stage, error_code, error_message, 
                    contract_version="v1"):
        
        correlation = self.get_correlation_context(trace_id)
        
        log_entry = {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "parent_trace_id": correlation.get("parent_trace_id"),
            "stage": stage,
            "event": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error_code": error_code,
            "error_message": error_message,
            "contract_version": contract_version
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def record_replay_lineage(self, trace_id, original_trace_id, lineage_depth=1):
        
        correlation = self.get_correlation_context(trace_id)
        
        log_entry = {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "parent_trace_id": original_trace_id,
            "event": "replay_lineage",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "original_trace_id": original_trace_id,
            "lineage_depth": lineage_depth
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def record_orchestration_transition(self, trace_id, from_stage, to_stage, 
                                       transition_type="normal"):
        
        correlation = self.get_correlation_context(trace_id)
        
        log_entry = {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "event": "orchestration_transition",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "from_stage": from_stage,
            "to_stage": to_stage,
            "transition_type": transition_type
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def record_dependency_status(self, trace_id, dependency_name, status, 
                                details=None):
        
        correlation = self.get_correlation_context(trace_id)
        
        log_entry = {
            "trace_id": trace_id,
            "correlation_id": correlation.get("correlation_id"),
            "event": "dependency_status",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dependency_name": dependency_name,
            "status": status,
            "details": details
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def _append_log(self, log_entry):
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry, default=str) + "\n")
    
    def get_trace_logs(self, trace_id):
        
        return [log for log in self.logs if log.get("trace_id") == trace_id]
    
    def get_correlation_group(self, correlation_id):
        
        return [log for log in self.logs if log.get("correlation_id") == correlation_id]
    
    def generate_distributed_trace_report(self, trace_id):
        
        correlation = self.get_correlation_context(trace_id)
        trace_logs = self.get_trace_logs(trace_id)
        
        
        events_by_type = {}
        for log in trace_logs:
            event_type = log.get("event", "unknown")
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(log)
        
        
        stage_entries = {log["stage"]: log for log in trace_logs if log.get("event") == "stage_entry"}
        stage_latencies = {}
        for log in trace_logs:
            if log.get("event") == "stage_exit":
                stage = log.get("stage")
                latency = log.get("latency_ms", 0)
                stage_latencies[stage] = latency
        
        return {
            "trace_id": trace_id,
            "correlation_context": correlation,
            "total_events": len(trace_logs),
            "events_by_type": events_by_type,
            "stage_latencies": stage_latencies,
            "dependency_statuses": [
                log for log in trace_logs if log.get("event") == "dependency_status"
            ],
            "events": trace_logs
        }
    
    def get_stage_latencies(self, trace_id):
        
        trace_logs = self.get_trace_logs(trace_id)
        latencies = {}
        
        for log in trace_logs:
            if log.get("event") == "stage_exit" and "latency_ms" in log:
                stage = log["stage"]
                if stage not in latencies:
                    latencies[stage] = []
                latencies[stage].append(log["latency_ms"])
        
        
        return {stage: round(sum(times) / len(times), 2) for stage, times in latencies.items()}



_global_tracker = None


def get_tracker():
    
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ObservabilityTracker()
    return _global_tracker


def reset_tracker():
    
    global _global_tracker
    _global_tracker = None
