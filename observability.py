import json
import time
from datetime import datetime
from pathlib import Path


class ObservabilityTracker:
    
    
    def __init__(self, log_file="observability.log"):
        self.log_file = log_file
        self.logs = []
        self._load_existing_logs()
    
    def _load_existing_logs(self):
        """Load existing logs from file."""
        if Path(self.log_file).exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            self.logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    
    def record_stage_entry(self, trace_id, stage, contract_version="v1", replay_mode=False):
        """Record entry into a pipeline stage."""
        entry_time = time.time()
        return {
            "trace_id": trace_id,
            "stage": stage,
            "event": "stage_entry",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "contract_version": contract_version,
            "replay_mode": replay_mode,
            "entry_time": entry_time
        }
    
    def record_stage_exit(self, trace_id, stage, entry_time, decision_state=None, 
                         success=True, contract_version="v1", replay_mode=False):
        """Record exit from a pipeline stage with latency."""
        exit_time = time.time()
        latency_ms = round((exit_time - entry_time) * 1000, 2)
        
        log_entry = {
            "trace_id": trace_id,
            "stage": stage,
            "event": "stage_exit",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "latency_ms": latency_ms,
            "contract_version": contract_version,
            "replay_mode": replay_mode,
            "decision_state": decision_state,
            "success": success
        }
        
        self.logs.append(log_entry)
        self._append_log(log_entry)
        return log_entry
    
    def record_decision(self, trace_id, stage, decision_state, confidence, score,
                       contract_version="v1", replay_mode=False):
        """Record a decision point with uncertainty state."""
        log_entry = {
            "trace_id": trace_id,
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
        """Record an error event."""
        log_entry = {
            "trace_id": trace_id,
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
    
    def _append_log(self, log_entry):
        """Append log entry to file (append-only)."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry, default=str) + "\n")
    
    def get_trace_logs(self, trace_id):
        """Retrieve all logs for a specific trace."""
        return [log for log in self.logs if log.get("trace_id") == trace_id]
    
    def get_stage_latencies(self, trace_id):
        """Get latency breakdown by stage."""
        trace_logs = self.get_trace_logs(trace_id)
        latencies = {}
        
        for log in trace_logs:
            if log.get("event") == "stage_exit" and "latency_ms" in log:
                stage = log["stage"]
                if stage not in latencies:
                    latencies[stage] = []
                latencies[stage].append(log["latency_ms"])
        
        # Compute averages
        return {stage: round(sum(times) / len(times), 2) for stage, times in latencies.items()}
    
    def export_logs(self):
        """Export all logs in memory."""
        return self.logs


# Global tracker instance
_tracker = None

def get_tracker():
    """Get or create global tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ObservabilityTracker()
    return _tracker
