

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple
from enum import Enum
import uuid


class VerificationNodeType(Enum):
    REPLAY_HASH_VERIFIER = "REPLAY_HASH_VERIFIER"
    TRACE_CONTINUITY_VERIFIER = "TRACE_CONTINUITY_VERIFIER"
    LINEAGE_INTEGRITY_VERIFIER = "LINEAGE_INTEGRITY_VERIFIER"
    GOVERNANCE_CONSTRAINT_VERIFIER = "GOVERNANCE_CONSTRAINT_VERIFIER"


class VerificationResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    INCONCLUSIVE = "INCONCLUSIVE"


class FederatedVerificationNode:
   
    
    def __init__(self, 
                 verifier_id: str,
                 verifier_type: VerificationNodeType):
        self.verifier_id = verifier_id
        self.verifier_type = verifier_type
        self.verification_log = []
        self.attestation_log = []
        self.consensus_queries = {}
    
    def verify_replay_hash(self,
                          trace_id: str,
                          execution_data: Dict[str, Any],
                          expected_hash: str) -> Tuple[VerificationResult, Dict[str, Any]]:
        
        computed_hash = self._compute_execution_hash(execution_data)
        
        result = VerificationResult.PASS if computed_hash == expected_hash else VerificationResult.FAIL
        
        verification_record = {
            "verification_id": f"VERIFY-{uuid.uuid4().hex[:8]}",
            "verifier_id": self.verifier_id,
            "verifier_type": self.verifier_type.value,
            "trace_id": trace_id,
            "verification_type": "REPLAY_HASH",
            "result": result.value,
            "expected_hash": expected_hash,
            "computed_hash": computed_hash,
            "hash_match": computed_hash == expected_hash,
            "verification_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.verification_log.append(verification_record)
        return result, verification_record
    
    def verify_trace_continuity(self,
                               trace_id: str,
                               execution_stages: List[Tuple[str, Dict[str, Any]]]) -> Tuple[VerificationResult, Dict[str, Any]]:
        
        all_match = True
        mismatches = []
        
        for stage_name, stage_output in execution_stages:
            stage_trace_id = stage_output.get("trace_id")
            if stage_trace_id != trace_id:
                all_match = False
                mismatches.append({
                    "stage": stage_name,
                    "expected_trace_id": trace_id,
                    "actual_trace_id": stage_trace_id
                })
        
        result = VerificationResult.PASS if all_match else VerificationResult.FAIL
        
        verification_record = {
            "verification_id": f"VERIFY-{uuid.uuid4().hex[:8]}",
            "verifier_id": self.verifier_id,
            "verifier_type": self.verifier_type.value,
            "trace_id": trace_id,
            "verification_type": "TRACE_CONTINUITY",
            "result": result.value,
            "stages_checked": len(execution_stages),
            "all_match": all_match,
            "mismatches": mismatches,
            "verification_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.verification_log.append(verification_record)
        return result, verification_record
    
    def verify_lineage_integrity(self,
                                trace_id: str,
                                lineage_entries: List[Dict[str, Any]],
                                expected_lineage_hash: str) -> Tuple[VerificationResult, Dict[str, Any]]:
        
        issues = []
        
        
        for i, entry in enumerate(lineage_entries):
            if entry.get("sequence") != i + 1:
                issues.append({
                    "issue": "sequence_inconsistent",
                    "index": i,
                    "expected_sequence": i + 1,
                    "actual_sequence": entry.get("sequence")
                })
        
        
        event_ids = {e.get("event_id") for e in lineage_entries}
        for entry in lineage_entries:
            parent_id = entry.get("parent_event_id")
            if parent_id and parent_id not in event_ids:
                issues.append({
                    "issue": "orphaned_parent_reference",
                    "event_id": entry.get("event_id"),
                    "parent_id": parent_id
                })
        
        
        computed_lineage_hash = self._compute_lineage_hash(lineage_entries)
        hash_match = computed_lineage_hash == expected_lineage_hash
        if not hash_match:
            issues.append({
                "issue": "lineage_hash_mismatch",
                "expected": expected_lineage_hash,
                "computed": computed_lineage_hash
            })
        
        result = VerificationResult.PASS if not issues else VerificationResult.FAIL
        
        verification_record = {
            "verification_id": f"VERIFY-{uuid.uuid4().hex[:8]}",
            "verifier_id": self.verifier_id,
            "verifier_type": self.verifier_type.value,
            "trace_id": trace_id,
            "verification_type": "LINEAGE_INTEGRITY",
            "result": result.value,
            "lineage_entries_checked": len(lineage_entries),
            "issues_found": len(issues),
            "issues": issues,
            "expected_lineage_hash": expected_lineage_hash,
            "computed_lineage_hash": computed_lineage_hash,
            "verification_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.verification_log.append(verification_record)
        return result, verification_record
    
    def verify_governance_constraint(self,
                                    trace_id: str,
                                    execution_record: Dict[str, Any]) -> Tuple[VerificationResult, Dict[str, Any]]:
        
        constraints_verified = []
        constraints_violated = []
        
        
        sanskar_output = execution_record.get("stages", {}).get("sanskar", {})
        if sanskar_output:
            
            if "authority_escalation" in sanskar_output:
                constraints_violated.append({
                    "constraint": "NO_AUTHORITY_ESCALATION",
                    "violation": "Sanskar attempted authority escalation"
                })
            else:
                constraints_verified.append({
                    "constraint": "NO_AUTHORITY_ESCALATION",
                    "status": "VERIFIED"
                })
        
        
        rajya_output = execution_record.get("stages", {}).get("rajya", {})
        if rajya_output:
            governance_validation = rajya_output.get("governance_validation", {})
            
            
            if governance_validation.get("external_constraint_maintained"):
                constraints_verified.append({
                    "constraint": "EXTERNAL_CONSTRAINT_MAINTAINED",
                    "status": "VERIFIED"
                })
            else:
                constraints_violated.append({
                    "constraint": "EXTERNAL_CONSTRAINT_MAINTAINED",
                    "violation": "External constraint was compromised"
                })
            
            
            if not governance_validation.get("authority_delegation"):
                constraints_verified.append({
                    "constraint": "NO_AUTHORITY_DELEGATION",
                    "status": "VERIFIED"
                })
            else:
                constraints_violated.append({
                    "constraint": "NO_AUTHORITY_DELEGATION",
                    "violation": "Authority was delegated to intelligence layer"
                })
        
        
        enforcement_output = execution_record.get("stages", {}).get("enforcement", {})
        if enforcement_output:
            
            if "authorized_execution" not in enforcement_output or enforcement_output["authorized_execution"]:
                constraints_verified.append({
                    "constraint": "ENFORCEMENT_REQUIRES_AUTHORIZATION",
                    "status": "VERIFIED"
                })
            else:
                constraints_violated.append({
                    "constraint": "ENFORCEMENT_REQUIRES_AUTHORIZATION",
                    "violation": "Enforcement executed without proper authorization"
                })
        
       
        sanskar_confidence = sanskar_output.get("intelligence_output", {}).get("confidence", 0)
        if sanskar_confidence > 0.8:
            
            if not rajya_output.get("governance_validation", {}).get("external_constraint_maintained"):
                constraints_violated.append({
                    "constraint": "NO_CONFIDENCE_ESCALATION",
                    "violation": "High confidence incorrectly escalated to authority"
                })
            else:
                constraints_verified.append({
                    "constraint": "NO_CONFIDENCE_ESCALATION",
                    "status": "VERIFIED",
                    "note": "High confidence correctly bounded by governance"
                })
        
        
        if constraints_violated:
            result = VerificationResult.FAIL
        elif constraints_verified:
            result = VerificationResult.PASS
        else:
            result = VerificationResult.INCONCLUSIVE
        
        verification_record = {
            "verification_id": f"VERIFY-{uuid.uuid4().hex[:8]}",
            "verifier_id": self.verifier_id,
            "verifier_type": self.verifier_type.value,
            "trace_id": trace_id,
            "verification_type": "GOVERNANCE_CONSTRAINT",
            "result": result.value,
            "constraints_verified": constraints_verified,
            "constraints_violated": constraints_violated,
            "total_constraints_checked": len(constraints_verified) + len(constraints_violated),
            "governance_status": "COMPLIANT" if not constraints_violated else "VIOLATED",
            "verification_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.verification_log.append(verification_record)
        return result, verification_record
    
    def issue_attestation(self,
                         trace_id: str,
                         verification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        all_pass = all(v.get("result") == "PASS" for v in verification_results)
        
        attestation = {
            "attestation_id": f"ATT-{uuid.uuid4().hex[:8]}",
            "verifier_id": self.verifier_id,
            "verifier_type": self.verifier_type.value,
            "trace_id": trace_id,
            "attestation_timestamp": datetime.utcnow().isoformat() + "Z",
            "attestation_verdict": "PASS" if all_pass else "FAIL",
            "verifications_included": len(verification_results),
            "verification_results": verification_results,
            "attestation_signature": self._sign_attestation(trace_id, verification_results)
        }
        
        self.attestation_log.append(attestation)
        return attestation
    
    def query_federated_consensus(self,
                                 trace_id: str,
                                 other_verifiers: List['FederatedVerificationNode']) -> Dict[str, Any]:
        
        consensus_query = {
            "query_id": f"CONSENSUS-{uuid.uuid4().hex[:8]}",
            "trace_id": trace_id,
            "querying_verifier": self.verifier_id,
            "consensus_timestamp": datetime.utcnow().isoformat() + "Z",
            "verifiers_queried": len(other_verifiers),
            "verifier_responses": []
        }
        
        for verifier in other_verifiers:
            
            recent_verifications = [v for v in verifier.verification_log 
                                   if v.get("trace_id") == trace_id]
            if recent_verifications:
                response = {
                    "verifier_id": verifier.verifier_id,
                    "verifier_type": verifier.verifier_type.value,
                    "last_verification": recent_verifications[-1]
                }
                consensus_query["verifier_responses"].append(response)
        
        
        passes = sum(1 for r in consensus_query["verifier_responses"] 
                    if r.get("last_verification", {}).get("result") == "PASS")
        total = len(consensus_query["verifier_responses"])
        
        consensus_query["consensus_result"] = {
            "verifiers_passed": passes,
            "verifiers_total": total,
            "consensus_achieved": passes >= (total // 2 + 1),
            "consensus_verdict": "PASS" if passes >= (total // 2 + 1) else "FAIL"
        }
        
        self.consensus_queries[consensus_query["query_id"]] = consensus_query
        return consensus_query
    
    def _compute_execution_hash(self, data: Dict[str, Any]) -> str:
        
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def _compute_lineage_hash(self, lineage_entries: List[Dict[str, Any]]) -> str:
        
        sorted_entries = sorted(
            lineage_entries,
            key=lambda x: x.get("sequence", 0)
        )
        serialized = json.dumps(sorted_entries, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def _sign_attestation(self, trace_id: str, verification_results: List[Dict[str, Any]]) -> str:
        
        data = {
            "trace_id": trace_id,
            "verification_results": verification_results,
            "verifier_id": self.verifier_id
        }
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def get_verification_summary(self) -> Dict[str, Any]:
        
        verification_types = {}
        results = {"PASS": 0, "FAIL": 0, "PARTIAL": 0, "INCONCLUSIVE": 0}
        
        for v in self.verification_log:
            vtype = v.get("verification_type", "UNKNOWN")
            result = v.get("result", "UNKNOWN")
            
            verification_types[vtype] = verification_types.get(vtype, 0) + 1
            results[result] = results.get(result, 0) + 1
        
        return {
            "verifier_id": self.verifier_id,
            "verifier_type": self.verifier_type.value,
            "total_verifications": len(self.verification_log),
            "by_type": verification_types,
            "by_result": results,
            "attestations_issued": len(self.attestation_log),
            "consensus_queries": len(self.consensus_queries)
        }


class FederatedVerificationCluster:
    
    
    def __init__(self):
        self.verifiers = {}
        self.consensus_requirements = {}
    
    def add_verifier(self, verifier: FederatedVerificationNode):
        """Add a verifier to the cluster."""
        self.verifiers[verifier.verifier_id] = verifier
    
    def perform_federated_verification(self,
                                      trace_id: str,
                                      execution_record: Dict[str, Any]) -> Dict[str, Any]:
        
        federated_result = {
            "trace_id": trace_id,
            "federated_verification_timestamp": datetime.utcnow().isoformat() + "Z",
            "verifiers_count": len(self.verifiers),
            "verifications_by_verifier": {},
            "federated_consensus": None
        }
        
        stages = execution_record.get("stages", {})
        
        for verifier_id, verifier in self.verifiers.items():
            verifier_results = []
            
            
            bucket_response = stages.get("bucket", {})
            if bucket_response.get("persistence"):
                lineage_hash = bucket_response["persistence"].get("lineage_hash")
                result, record = verifier.verify_replay_hash(trace_id, stages, lineage_hash or "")
                verifier_results.append(record)
            
            
            execution_stages = [(name, stage) for name, stage in stages.items()]
            result, record = verifier.verify_trace_continuity(trace_id, execution_stages)
            verifier_results.append(record)
            
            
            result, record = verifier.verify_governance_constraint(trace_id, execution_record)
            verifier_results.append(record)
            
            
            attestation = verifier.issue_attestation(trace_id, verifier_results)
            
            federated_result["verifications_by_verifier"][verifier_id] = {
                "verifications": verifier_results,
                "attestation": attestation
            }
        
        
        all_verifiers = list(self.verifiers.values())
        if all_verifiers:
            primary_verifier = all_verifiers[0]
            consensus = primary_verifier.query_federated_consensus(trace_id, all_verifiers[1:])
            federated_result["federated_consensus"] = consensus
        
        return federated_result
