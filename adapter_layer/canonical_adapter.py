#!/usr/bin/env python3


from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict, field
import json
import hashlib
from datetime import datetime


class ContractPhase(Enum):
    
    SIGNAL_SOURCE = "signal_source"
    SANSKAR = "sanskar"
    RAJYA = "rajya"
    ENFORCEMENT = "enforcement"
    BUCKET = "bucket"
    INSIGHT_BRIDGE = "insight_bridge"


class ContractOwnership(Enum):
    
    SIGNAL_SOURCE_OWNER = "signal_source"
    SANSKAR_OWNER = "sanskar"
    RAJYA_OWNER = "rajya"
    ENFORCEMENT_OWNER = "enforcement"
    BUCKET_OWNER = "bucket"
    INSIGHT_BRIDGE_OWNER = "insight_bridge"


class FailureMode(Enum):
    
    TIMEOUT = "timeout"
    REJECTION = "rejection"
    SCHEMA_MISMATCH = "schema_mismatch"
    VERSION_INCOMPATIBILITY = "version_incompatibility"
    TRACE_MUTATION = "trace_mutation"
    MISSING_LINEAGE = "missing_lineage"
    DUPLICATE_EVENT = "duplicate_event"
    MISSING_PARTICIPANT_RESPONSE = "missing_participant_response"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    GOVERNANCE_VIOLATION = "governance_violation"


@dataclass
class TraceContext:
    
    trace_id: str
    parent_span_id: Optional[str] = None
    span_id: Optional[str] = None
    correlation_id: Optional[str] = None
    origin_phase: ContractPhase = ContractPhase.SIGNAL_SOURCE
    
    def validate_immutability(self) -> bool:
        
        return bool(self.trace_id)
    
    def declare_ownership(self, phase: ContractPhase) -> Dict[str, Any]:
        
        return {
            "trace_id": self.trace_id,
            "owned_by_phase": phase.value,
            "timestamp": datetime.utcnow().isoformat()
        }


@dataclass
class ContractHeader:
    
    version: str
    schema_owner: ContractOwnership
    trace_context: TraceContext
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_phase: ContractPhase = ContractPhase.SIGNAL_SOURCE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "schema_owner": self.schema_owner.value,
            "trace_context": asdict(self.trace_context),
            "timestamp": self.timestamp,
            "source_phase": self.source_phase.value
        }


@dataclass
class ContractPayload:
    
    data: Dict[str, Any]
    schema_version: str
    payload_hash: str = field(default="")
    
    def __post_init__(self):
        
        if not self.payload_hash:
            content = json.dumps(self.data, sort_keys=True)
            self.payload_hash = hashlib.sha256(content.encode()).hexdigest()
    
    def verify_hash(self) -> bool:
        
        content = json.dumps(self.data, sort_keys=True)
        calculated_hash = hashlib.sha256(content.encode()).hexdigest()
        return calculated_hash == self.payload_hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "schema_version": self.schema_version,
            "payload_hash": self.payload_hash
        }


@dataclass
class Contract:
    
    header: ContractHeader
    payload: ContractPayload
    lineage: List[str] = field(default_factory=list)
    
    def add_lineage_entry(self, phase: ContractPhase) -> None:
        
        entry = f"{phase.value}:{datetime.utcnow().isoformat()}"
        self.lineage.append(entry)
    
    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        
        required_keys = schema.get("required_keys", [])
        for key in required_keys:
            if key not in self.payload.data:
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict(),
            "lineage": self.lineage
        }
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)


class CanonicalAdapter:
    
    
    def __init__(self, phase: ContractPhase, owner: ContractOwnership):
        self.phase = phase
        self.owner = owner
        self.failure_log: List[Dict[str, Any]] = []
        self.schema_registry: Dict[str, Dict[str, Any]] = {}
    
    def register_schema(self, version: str, schema: Dict[str, Any]) -> None:
        
        self.schema_registry[version] = schema
    
    def validate_schema_compatibility(
        self, 
        incoming_version: str, 
        current_version: str
    ) -> Tuple[bool, Optional[str]]:
        
        if incoming_version == current_version:
            return True, None
        
        
        try:
            incoming_parts = [int(x) for x in incoming_version.split(".")]
            current_parts = [int(x) for x in current_version.split(".")]
        except ValueError:
            return False, f"Invalid version format: {incoming_version} or {current_version}"
        
        
        if (incoming_parts[0] == current_parts[0] and 
            incoming_parts[1] <= current_parts[1]):
            return True, None
        
        return False, f"Version {incoming_version} incompatible with {current_version}"
    
    def validate_contract(
        self, 
        contract: Contract, 
        expected_version: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        
        errors = []
        
        
        if not contract.header.trace_context.validate_immutability():
            errors.append("TRACE_MUTATION: trace_id is missing or invalid")
        
        
        if not contract.payload.verify_hash():
            errors.append(f"TRACE_MUTATION: payload hash mismatch")
            self._log_failure(FailureMode.TRACE_MUTATION, contract)
        
        
        if not contract.validate_schema(self.schema_registry.get(
            contract.payload.schema_version, 
            {}
        )):
            errors.append(f"SCHEMA_MISMATCH: missing required fields")
            self._log_failure(FailureMode.SCHEMA_MISMATCH, contract)
        
        
        if expected_version:
            compatible, msg = self.validate_schema_compatibility(
                contract.payload.schema_version,
                expected_version
            )
            if not compatible:
                errors.append(f"VERSION_INCOMPATIBILITY: {msg}")
                self._log_failure(FailureMode.VERSION_INCOMPATIBILITY, contract)
        
        
        if not contract.lineage:
            errors.append("MISSING_LINEAGE: contract has no phase lineage")
            self._log_failure(FailureMode.MISSING_LINEAGE, contract)
        
        return len(errors) == 0, errors
    
    def process_contract(
        self, 
        contract: Contract
    ) -> Tuple[Contract, bool, Optional[str]]:
        
        valid, errors = self.validate_contract(contract)
        if not valid:
            error_msg = "; ".join(errors)
            self._log_failure(FailureMode.SCHEMA_MISMATCH, contract, error_msg)
            return contract, False, error_msg
        
        
        contract.add_lineage_entry(self.phase)
        
        
        contract.header.schema_owner = self.owner
        
        return contract, True, None
    
    def _log_failure(
        self, 
        mode: FailureMode, 
        contract: Contract, 
        detail: Optional[str] = None
    ) -> None:
        
        failure_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": self.phase.value,
            "failure_mode": mode.value,
            "trace_id": contract.header.trace_context.trace_id,
            "detail": detail or ""
        }
        self.failure_log.append(failure_record)
    
    def get_failure_visibility_report(self) -> Dict[str, Any]:
        
        failure_counts = {}
        for failure in self.failure_log:
            mode = failure["failure_mode"]
            failure_counts[mode] = failure_counts.get(mode, 0) + 1
        
        return {
            "phase": self.phase.value,
            "total_failures": len(self.failure_log),
            "failure_breakdown": failure_counts,
            "recent_failures": self.failure_log[-5:]  # Last 5
        }


class ContractRegistry:
    
    
    def __init__(self):
        self.contracts: List[Contract] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.adapters: Dict[ContractPhase, CanonicalAdapter] = {}
    
    def register_adapter(self, adapter: CanonicalAdapter) -> None:
        
        self.adapters[adapter.phase] = adapter
    
    def register_schema(
        self, 
        owner: ContractOwnership, 
        version: str, 
        schema: Dict[str, Any]
    ) -> None:
        
        key = f"{owner.value}:{version}"
        self.schemas[key] = schema
    
    def process_through_chain(
        self, 
        contract: Contract
    ) -> Tuple[Contract, bool, List[Dict[str, Any]]]:
        
        audit_trail = []
        current_contract = contract
        
        for phase in [
            ContractPhase.SANSKAR,
            ContractPhase.RAJYA,
            ContractPhase.ENFORCEMENT,
            ContractPhase.BUCKET,
            ContractPhase.INSIGHT_BRIDGE
        ]:
            adapter = self.adapters.get(phase)
            if not adapter:
                audit_trail.append({
                    "phase": phase.value,
                    "status": "SKIPPED",
                    "reason": "no_adapter_registered"
                })
                continue
            
            updated_contract, success, error = adapter.process_contract(current_contract)
            
            audit_trail.append({
                "phase": phase.value,
                "status": "SUCCESS" if success else "FAILURE",
                "error": error,
                "trace_id": updated_contract.header.trace_context.trace_id
            })
            
            if not success:
                return updated_contract, False, audit_trail
            
            current_contract = updated_contract
        
        self.contracts.append(current_contract)
        return current_contract, True, audit_trail
    
    def get_full_lineage(self, trace_id: str) -> Optional[List[str]]:
        
        for contract in self.contracts:
            if contract.header.trace_context.trace_id == trace_id:
                return contract.lineage
        return None
    
    def generate_registry_report(self) -> Dict[str, Any]:
        
        return {
            "total_contracts_processed": len(self.contracts),
            "registered_schemas": len(self.schemas),
            "registered_adapters": [phase.value for phase in self.adapters.keys()],
            "failure_reports": [
                adapter.get_failure_visibility_report() 
                for adapter in self.adapters.values()
            ]
        }
