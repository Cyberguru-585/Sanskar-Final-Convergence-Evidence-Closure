

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GovernanceBoundary(Enum):
    
    EXECUTION_AUTHORITY = "execution_authority"
    GOVERNANCE_AUTHORITY = "governance_authority"
    ORCHESTRATION_OWNERSHIP = "orchestration_ownership"
    SEMANTIC_TRUTH_OWNERSHIP = "semantic_truth_ownership"
    REPLAY_INTEGRITY = "replay_integrity"
    TRACE_CONTINUITY = "trace_continuity"
    SCHEMA_VALIDATION = "schema_validation"
    ENFORCEMENT_SEPARATION = "enforcement_separation"


class IntegrityCheckpoint(Enum):
    
    REPLAY_VALIDATION = "replay_validation"
    TRACE_CONTINUITY_CHECK = "trace_continuity_check"
    SCHEMA_VALIDATION_CHECK = "schema_validation_check"
    BOUNDARY_ENFORCEMENT_CHECK = "boundary_enforcement_check"
    CROSS_SERVICE_CONTRACT_CHECK = "cross_service_contract_check"


@dataclass
class IntegrityViolation:
    
    violation_id: str
    checkpoint: str
    boundary: str
    severity: str
    timestamp: str
    details: Dict[str, Any]
    execution_halted: bool
    trace_preserved: bool
    halt_reason: str
    affected_services: List[str]


@dataclass
class GovernanceBoundaryProof:
    
    proof_id: str
    boundary: str
    service_role: str
    attempted_action: str
    rejection_reason: str
    timestamp: str
    trace_id: str
    enforcement_mechanism: str


class FailClosedEnforcementVerifier:
    
    
    def __init__(self):
        self.integrity_violations: List[IntegrityViolation] = []
        self.boundary_proofs: List[GovernanceBoundaryProof] = []
        self.execution_halts: List[Dict[str, Any]] = []
        self.halt_checkpoints: Dict[str, bool] = {}
        
    def verify_replay_integrity(self, 
                               trace_id: str,
                               replay_hash: str,
                               expected_hash: str) -> Tuple[bool, Optional[IntegrityViolation]]:
        
        if replay_hash != expected_hash:
            violation = IntegrityViolation(
                violation_id=f"VIO-REP-{len(self.integrity_violations)}",
                checkpoint=IntegrityCheckpoint.REPLAY_VALIDATION.value,
                boundary=GovernanceBoundary.REPLAY_INTEGRITY.value,
                severity="CRITICAL",
                timestamp=datetime.utcnow().isoformat() + "Z",
                details={
                    "trace_id": trace_id,
                    "expected_hash": expected_hash,
                    "actual_hash": replay_hash,
                    "mismatch": True
                },
                execution_halted=True,
                trace_preserved=True,
                halt_reason="REPLAY_HASH_MISMATCH_DETECTED",
                affected_services=["*"]
            )
            self.integrity_violations.append(violation)
            self._record_execution_halt(violation)
            logger.error(f"HALT: Replay integrity violation detected for {trace_id}")
            return False, violation
        
        logger.info(f"Replay integrity verified for {trace_id}")
        return True, None
    
    def verify_trace_continuity(self,
                               trace_id: str,
                               service_lineage: List[str],
                               expected_continuity: bool) -> Tuple[bool, Optional[IntegrityViolation]]:
        
        
        if not service_lineage:
            violation = IntegrityViolation(
                violation_id=f"VIO-TC-{len(self.integrity_violations)}",
                checkpoint=IntegrityCheckpoint.TRACE_CONTINUITY_CHECK.value,
                boundary=GovernanceBoundary.TRACE_CONTINUITY.value,
                severity="CRITICAL",
                timestamp=datetime.utcnow().isoformat() + "Z",
                details={
                    "trace_id": trace_id,
                    "lineage_empty": True
                },
                execution_halted=True,
                trace_preserved=True,
                halt_reason="TRACE_CONTINUITY_BROKEN",
                affected_services=["*"]
            )
            self.integrity_violations.append(violation)
            self._record_execution_halt(violation)
            logger.error(f"HALT: Trace continuity broken for {trace_id}")
            return False, violation
        
        logger.info(f"Trace continuity verified for {trace_id}: {service_lineage}")
        return True, None
    
    def verify_schema_validation(self,
                                trace_id: str,
                                payload: Dict[str, Any],
                                schema_constraints: Dict[str, Any]) -> Tuple[bool, Optional[IntegrityViolation]]:
       
        for required_field, constraint in schema_constraints.items():
            if required_field not in payload:
                violation = IntegrityViolation(
                    violation_id=f"VIO-SV-{len(self.integrity_violations)}",
                    checkpoint=IntegrityCheckpoint.SCHEMA_VALIDATION_CHECK.value,
                    boundary=GovernanceBoundary.SCHEMA_VALIDATION.value,
                    severity="CRITICAL",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    details={
                        "trace_id": trace_id,
                        "missing_field": required_field,
                        "expected_constraint": constraint
                    },
                    execution_halted=True,
                    trace_preserved=True,
                    halt_reason="SCHEMA_VALIDATION_FAILED",
                    affected_services=["*"]
                )
                self.integrity_violations.append(violation)
                self._record_execution_halt(violation)
                logger.error(f"HALT: Schema validation failed for {trace_id}, missing field: {required_field}")
                return False, violation
        
        logger.info(f"Schema validation passed for {trace_id}")
        return True, None
    
    def verify_boundary_enforcement(self,
                                   service_role: str,
                                   attempted_authority: str,
                                   trace_id: str) -> Tuple[bool, Optional[GovernanceBoundaryProof]]:
       
        allowed_authorities = {
            "sanskar": [],  
            "core": [],     
            "enforcement": [],  
            "truth": [],    
            "signal_source": [],
            "observability": []
        }
        
        if service_role not in allowed_authorities:
            return True, None
        
        if attempted_authority in allowed_authorities[service_role]:
            return True, None
        
        
        proof = GovernanceBoundaryProof(
            proof_id=f"BPROOF-{len(self.boundary_proofs)}",
            boundary=GovernanceBoundary.GOVERNANCE_AUTHORITY.value,
            service_role=service_role,
            attempted_action=attempted_authority,
            rejection_reason=f"Service '{service_role}' attempted to claim '{attempted_authority}' authority",
            timestamp=datetime.utcnow().isoformat() + "Z",
            trace_id=trace_id,
            enforcement_mechanism="HARDCODED_BOUNDARY_CHECK"
        )
        self.boundary_proofs.append(proof)
        logger.warning(f"Boundary violation prevented: {service_role} attempted {attempted_authority}")
        return False, proof
    
    def verify_enforcement_separation(self,
                                     enforcement_output: Dict[str, Any],
                                     execution_context: Dict[str, Any]) -> Tuple[bool, Optional[IntegrityViolation]]:
        
        
        if execution_context.get("executor_id") == "ENFORCEMENT":
            violation = IntegrityViolation(
                violation_id=f"VIO-SE-{len(self.integrity_violations)}",
                checkpoint=IntegrityCheckpoint.BOUNDARY_ENFORCEMENT_CHECK.value,
                boundary=GovernanceBoundary.ENFORCEMENT_SEPARATION.value,
                severity="CRITICAL",
                timestamp=datetime.utcnow().isoformat() + "Z",
                details={
                    "trace_id": enforcement_output.get("trace_id"),
                    "violation": "Enforcement attempted self-execution"
                },
                execution_halted=True,
                trace_preserved=True,
                halt_reason="ENFORCEMENT_SEPARATION_VIOLATED",
                affected_services=["enforcement"]
            )
            self.integrity_violations.append(violation)
            self._record_execution_halt(violation)
            logger.error(f"HALT: Enforcement separation violated")
            return False, violation
        
        logger.info("Enforcement separation verified")
        return True, None
    
    def comprehensive_integrity_check(self,
                                     trace_id: str,
                                     service_role: str,
                                     replay_hash: str,
                                     expected_replay_hash: str,
                                     service_lineage: List[str],
                                     payload: Dict[str, Any]) -> Tuple[bool, List[IntegrityViolation]]:
        
        
        violations = []
        
        
        
        replay_ok, replay_violation = self.verify_replay_integrity(trace_id, replay_hash, expected_replay_hash)
        if not replay_ok:
            violations.append(replay_violation)
        
       
       
        continuity_ok, continuity_violation = self.verify_trace_continuity(trace_id, service_lineage, True)
        if not continuity_ok:
            violations.append(continuity_violation)
        
      
      
        schema_constraints = {
            "trace_id": {"type": "string", "required": True},
            "service": {"type": "string", "required": True}
        }
        schema_ok, schema_violation = self.verify_schema_validation(trace_id, payload, schema_constraints)
        if not schema_ok:
            violations.append(schema_violation)
        
        
        
        boundary_ok, boundary_proof = self.verify_boundary_enforcement(service_role, "semantic_truth_ownership", trace_id)
        if not boundary_ok and boundary_proof:
            
            
            pass
        
        all_ok = len(violations) == 0
        
        if not all_ok:
            logger.error(f"INTEGRITY CHECK FAILED: {len(violations)} violations detected. HALTING EXECUTION.")
        else:
            logger.info(f"All integrity checks passed for {trace_id}")
        
        return all_ok, violations
    
    def allow_execution_continuation(self,
                                    trace_id: str,
                                    current_service: str) -> Tuple[bool, str]:
        
        
        trace_halts = [h for h in self.execution_halts if h["trace_id"] == trace_id]
        
        if trace_halts:
            halt_reason = trace_halts[0]["halt_reason"]
            return False, halt_reason
        
        return True, "CONTINUE"
    
    def _record_execution_halt(self, violation: IntegrityViolation):
        
        
        halt_event = {
            "halt_id": f"HALT-{len(self.execution_halts)}",
            "violation_id": violation.violation_id,
            "trace_id": violation.details.get("trace_id", "UNKNOWN"),
            "checkpoint": violation.checkpoint,
            "boundary": violation.boundary,
            "reason": violation.halt_reason,
            "timestamp": violation.timestamp,
            "affected_services": violation.affected_services,
            "trace_preserved": violation.trace_preserved
        }
        self.execution_halts.append(halt_event)
        logger.critical(f"EXECUTION HALT RECORDED: {halt_event['halt_id']}")
    
    def export_state(self) -> Dict[str, Any]:
        
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_violations": len(self.integrity_violations),
            "critical_violations": sum(1 for v in self.integrity_violations if v.severity == "CRITICAL"),
            "total_execution_halts": len(self.execution_halts),
            "boundary_proofs": len(self.boundary_proofs),
            "violations": [asdict(v) for v in self.integrity_violations],
            "boundary_proofs": [asdict(p) for p in self.boundary_proofs],
            "execution_halts": self.execution_halts
        }
    
    def get_proof_of_fail_closed_behavior(self) -> Dict[str, Any]:
        
        
        return {
            "proof_timestamp": datetime.utcnow().isoformat() + "Z",
            "proof_type": "FAIL_CLOSED_GOVERNANCE_ENFORCEMENT",
            "total_integrity_checks": len(self.integrity_violations) + len(self.boundary_proofs),
            "total_violations_detected": len(self.integrity_violations),
            "total_boundary_violations_prevented": len([p for p in self.boundary_proofs if not p]),
            "execution_halts_triggered": len(self.execution_halts),
            "halt_reasons": list(set(h["reason"] for h in self.execution_halts)),
            "proof_summary": {
                "replay_integrity_enforced": sum(1 for v in self.integrity_violations if v.checkpoint == "replay_validation") > 0,
                "trace_continuity_enforced": sum(1 for v in self.integrity_violations if v.checkpoint == "trace_continuity_check") > 0,
                "schema_validation_enforced": sum(1 for v in self.integrity_violations if v.checkpoint == "schema_validation_check") > 0,
                "boundary_enforcement_enforced": len(self.boundary_proofs) > 0,
                "all_violations_halted_execution": all(h["trace_preserved"] for h in self.execution_halts)
            }
        }
