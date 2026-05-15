import json
import hashlib
from datetime import datetime


class ExternalExecutor:
    
    
    def __init__(self, executor_id="EXECUTOR-001"):
        self.executor_id = executor_id
        self.verified_executions = []
        self.verification_log = []
    
    def issue_directive(self, directive, trace_id, stage="enforcement"):
        
        issuance_timestamp = datetime.utcnow().isoformat() + "Z"
        
        directive_payload = {
            "directive": directive,
            "trace_id": trace_id,
            "stage": stage,
            "issuance_timestamp": issuance_timestamp,
            "issued_by": stage,
            "status": "ISSUED",
            "awaiting_verification": True
        }
        
        return directive_payload
    
    def verify_execution(self, directive_payload, execution_result,
                        execution_completed=True, completion_hash=None):
        
        directive = directive_payload["directive"]
        directive_id = directive.get("directive_id", "UNKNOWN")
        
        verification_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Compute verification signature
        if completion_hash is None:
            completion_hash = self._compute_result_hash(execution_result)
        
        verification_payload = {
            "directive_id": directive_id,
            "trace_id": directive_payload["trace_id"],
            "executor_id": self.executor_id,
            "execution_verification": {
                "verified_by": self.executor_id,
                "execution_completed": execution_completed,
                "completion_hash": completion_hash,
                "verification_timestamp": verification_timestamp
            },
            "separation_of_concerns": {
                "issuance": {
                    "issued_by": directive_payload["issued_by"],
                    "issuance_timestamp": directive_payload["issuance_timestamp"],
                    "directive_id": directive_id
                },
                "verification": {
                    "verified_by": self.executor_id,
                    "verification_timestamp": verification_timestamp,
                    "result_hash": completion_hash
                }
            },
            "status": "VERIFIED" if execution_completed else "FAILED",
            "execution_result": execution_result
        }
        
        self.verified_executions.append(verification_payload)
        self.verification_log.append({
            "timestamp": verification_timestamp,
            "directive_id": directive_id,
            "trace_id": directive_payload["trace_id"],
            "status": verification_payload["status"]
        })
        
        return verification_payload
    
    def verify_separation_of_concerns(self, verification_payload):
       
        soc = verification_payload.get("separation_of_concerns", {})
        issuance = soc.get("issuance", {})
        verification = soc.get("verification", {})
        
        proof = {
            "separation_verified": True,
            "issuance": {
                "exists": bool(issuance),
                "issued_by": issuance.get("issued_by"),
                "timestamp": issuance.get("issuance_timestamp")
            },
            "verification": {
                "exists": bool(verification),
                "verified_by": verification.get("verified_by"),
                "timestamp": verification.get("verification_timestamp")
            },
            "issues": []
        }
        
        
        if issuance.get("issued_by") == verification.get("verified_by"):
            proof["issues"].append("WARNING: same entity issued and verified (consider multi-party verification)")
        
        if not issuance:
            proof["separation_verified"] = False
            proof["issues"].append("CRITICAL: issuance metadata missing")
        
        if not verification:
            proof["separation_verified"] = False
            proof["issues"].append("CRITICAL: verification metadata missing")
        
        proof["verdict"] = "PASS — clear separation of concerns" if proof["separation_verified"] else "FAIL — separation violated"
        
        return proof
    
    def batch_verify_executions(self, directive_payloads_and_results):
       
        verified_count = 0
        failed_count = 0
        verification_payloads = []
        
        for directive_payload, result, completed in directive_payloads_and_results:
            payload = self.verify_execution(directive_payload, result, completed)
            verification_payloads.append(payload)
            
            if completed:
                verified_count += 1
            else:
                failed_count += 1
        
        return {
            "batch_size": len(directive_payloads_and_results),
            "verified_count": verified_count,
            "failed_count": failed_count,
            "verification_rate": verified_count / len(directive_payloads_and_results) if directive_payloads_and_results else 0,
            "verifications": verification_payloads,
            "executor_id": self.executor_id
        }
    
    def get_verification_summary(self):
        """Get summary of all verifications."""
        return {
            "executor_id": self.executor_id,
            "total_verified": len(self.verified_executions),
            "successful": sum(1 for e in self.verified_executions if e["status"] == "VERIFIED"),
            "failed": sum(1 for e in self.verified_executions if e["status"] == "FAILED"),
            "verification_log": self.verification_log
        }
    
    def _compute_result_hash(self, execution_result):
        """Compute hash of execution result for verification."""
        result_data = {
            "result": execution_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        serialized = json.dumps(result_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def simulate_multi_executor_verification(directive_payload, execution_result,
                                        executor_ids=None):
   
    if executor_ids is None:
        executor_ids = ["EXECUTOR-001", "EXECUTOR-002", "EXECUTOR-003"]
    
    verifications = []
    consensus_hash = None
    
    for executor_id in executor_ids:
        executor = ExternalExecutor(executor_id)
        verification = executor.verify_execution(directive_payload, execution_result)
        verifications.append(verification)
        
        if consensus_hash is None:
            consensus_hash = verification["execution_verification"]["completion_hash"]
    
    # Check consensus
    hashes = [v["execution_verification"]["completion_hash"] for v in verifications]
    all_agree = len(set(hashes)) == 1
    
    return {
        "directive_id": directive_payload["directive"].get("directive_id"),
        "trace_id": directive_payload["trace_id"],
        "total_executors": len(executor_ids),
        "verifications": verifications,
        "consensus": {
            "all_executors_agree": all_agree,
            "consensus_hash": consensus_hash if all_agree else None,
            "hash_distribution": dict((h, sum(1 for hh in hashes if hh == h)) for h in set(hashes))
        },
        "verdict": "PASS — multi-executor consensus achieved" if all_agree else "FAIL — executor disagreement"
    }
