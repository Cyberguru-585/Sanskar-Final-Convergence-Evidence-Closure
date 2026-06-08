# runtime_adapters.py — Phase 2: Real Contract Wiring



import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)


@dataclass
class ContractViolation:
   
    adapter: str
    violation_type: str
    detail: str
    trace_id: str = "UNKNOWN"
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


class ContractSchema:
    
    
    REQUIRED_FIELDS = set()
    CONTRACT_VERSION = "v1"
    OWNER = "unknown"
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        
        if not isinstance(data, dict):
            return False, f"Expected dict, got {type(data).__name__}"
        
        missing = cls.REQUIRED_FIELDS - set(data.keys())
        if missing:
            return False, f"Missing required fields: {missing}"
        
        return True, "PASS"
    
    @classmethod
    def validate_field_type(cls, data: Dict, field: str, expected_type: type) -> Tuple[bool, str]:
        
        if field not in data:
            return False, f"Field {field} not found"
        if not isinstance(data[field], expected_type):
            return False, f"Field {field}: expected {expected_type.__name__}, got {type(data[field]).__name__}"
        return True, "PASS"


class IntelligenceOutputContract(ContractSchema):
   
    
    REQUIRED_FIELDS = {
        "trace_id",
        "stage",
        "entities",
        "ranking",
        "metadata"
    }
    CONTRACT_VERSION = "intelligence_output_v1"
    OWNER = "sanskar"  # Produced by SANSKAR
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        
        valid, msg = super().validate(data)
        if not valid:
            return False, msg
        
        
        if not isinstance(data.get("trace_id"), str) or not data["trace_id"]:
            return False, "trace_id must be non-empty string"
        
        
        if data.get("stage") != "sanskar":
            return False, f"stage must be 'sanskar', got {data.get('stage')}"
        
       
        if not isinstance(data.get("entities"), list):
            return False, "entities must be list"
        
        for i, entity in enumerate(data["entities"]):
            if not isinstance(entity, dict):
                return False, f"entities[{i}] must be dict"
            required_entity_fields = {"entity_id", "score", "confidence", "decision_state"}
            missing_entity = required_entity_fields - set(entity.keys())
            if missing_entity:
                return False, f"entities[{i}] missing fields: {missing_entity}"
            
            
            for field in ["score", "confidence"]:
                if not isinstance(entity[field], (int, float)):
                    return False, f"entities[{i}].{field} must be numeric"
                if not (0.0 <= entity[field] <= 1.0):
                    return False, f"entities[{i}].{field} must be in [0.0, 1.0]"
            
            
            valid_states = {"CONFIDENT", "AMBIGUOUS", "LOW_CONFIDENCE"}
            if entity["decision_state"] not in valid_states:
                return False, f"entities[{i}].decision_state must be one of {valid_states}"
        
       
        if not isinstance(data.get("ranking"), list):
            return False, "ranking must be list"
        
        entity_ids = {e["entity_id"] for e in data["entities"]}
        for rank_id in data["ranking"]:
            if rank_id not in entity_ids:
                return False, f"ranking references unknown entity_id: {rank_id}"
        
        
        if not isinstance(data.get("metadata"), dict):
            return False, "metadata must be dict"
        
        return True, "PASS"


class GovernanceDecisionContract(ContractSchema):
    
    
    REQUIRED_FIELDS = {
        "trace_id",
        "stage",
        "decision",
        "authority_check"
    }
    CONTRACT_VERSION = "governance_decision_v1"
    OWNER = "rajya"  
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        
        valid, msg = super().validate(data)
        if not valid:
            return False, msg
        
       
        auth = data.get("authority_check", {})
        if auth.get("decision_maker") != "rajya":
            return False, "Authority check failed: decision_maker must be 'rajya'"
        if auth.get("constitutional_authority") is not True:
            return False, "Authority check failed: constitutional_authority must be True"
        
        
        valid_decisions = {"APPROVED", "REJECTED", "DEFERRED"}
        if data.get("decision") not in valid_decisions:
            return False, f"decision must be one of {valid_decisions}"
        
        return True, "PASS"


class EventRecordContract(ContractSchema):
   
    
    REQUIRED_FIELDS = {
        "trace_id",
        "event_type",
        "event_data",
        "ownership"
    }
    CONTRACT_VERSION = "event_record_v1"
    OWNER = "bucket"  # Owned by Bucket, not SANSKAR
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        
        valid, msg = super().validate(data)
        if not valid:
            return False, msg
        
       
        ownership = data.get("ownership", {})
        if ownership.get("owner") != "bucket":
            return False, f"Ownership must declare 'bucket' as owner, got {ownership.get('owner')}"
        if ownership.get("immutable") is not True:
            return False, "Event must be marked immutable"
        
        return True, "PASS"


class SanskariToRajyaAdapter:
    
    
    def __init__(self):
        self.logger = logging.getLogger("adapter-sanskar-to-rajya")
        self.violation_log = []
        self.successful_crossings = 0
        
    def validate_and_forward(self, sanskar_output: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | ContractViolation]:
        
        trace_id = sanskar_output.get("trace_id", "UNKNOWN")
        
       
        valid, msg = IntelligenceOutputContract.validate(sanskar_output)
        if not valid:
            violation = ContractViolation(
                adapter="sanskar_to_rajya",
                violation_type="contract_validation",
                detail=msg,
                trace_id=trace_id
            )
            self.violation_log.append(asdict(violation))
            self.logger.error(f"Contract violation [trace_id={trace_id}]: {msg}")
            return False, violation
        
        
        forbidden_fields = {"enforcement_directive", "governance_decision", "bucket_write_direct"}
        if any(field in sanskar_output for field in forbidden_fields):
            violation = ContractViolation(
                adapter="sanskar_to_rajya",
                violation_type="authority_violation",
                detail=f"SANSKAR emitted forbidden field(s): {forbidden_fields & set(sanskar_output.keys())}",
                trace_id=trace_id
            )
            self.violation_log.append(asdict(violation))
            self.logger.error(f"Authority violation [trace_id={trace_id}]: {violation.detail}")
            return False, violation
        
        
        if "failure" in sanskar_output:
            
            failure = sanskar_output["failure"]
            if failure.get("trace_preserved") is False and "stage" in failure:
                self.logger.warning(f"Trace not preserved at failure [trace_id={trace_id}]")
        
        sanskar_output["contract_version"] = "intelligence_output_v1"
        
        self.successful_crossings += 1
        self.logger.info(f"Contract validated [trace_id={trace_id}] — forwarding to RAJYA")
        
        return True, sanskar_output
    
    def get_violation_log(self) -> List[Dict]:
        return self.violation_log
    
    def get_stats(self) -> Dict:
        return {
            "adapter": "sanskar_to_rajya",
            "successful_crossings": self.successful_crossings,
            "violations": len(self.violation_log),
            "violation_details": self.violation_log
        }


class RajyaToEnforcementAdapter:
  
    
    def __init__(self):
        self.logger = logging.getLogger("adapter-rajya-to-enforcement")
        self.violation_log = []
        self.successful_crossings = 0
        
    def validate_and_forward(self, rajya_decision: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | ContractViolation]:
       
        trace_id = rajya_decision.get("trace_id", "UNKNOWN")
        
        valid, msg = GovernanceDecisionContract.validate(rajya_decision)
        if not valid:
            violation = ContractViolation(
                adapter="rajya_to_enforcement",
                violation_type="contract_validation",
                detail=msg,
                trace_id=trace_id
            )
            self.violation_log.append(asdict(violation))
            self.logger.error(f"Contract violation [trace_id={trace_id}]: {msg}")
            return False, violation
        
        
        if rajya_decision.get("authority_check", {}).get("decision_maker") != "rajya":
            violation = ContractViolation(
                adapter="rajya_to_enforcement",
                violation_type="authority_violation",
                detail="Decision does not come from RAJYA",
                trace_id=trace_id
            )
            self.violation_log.append(asdict(violation))
            self.logger.error(f"Authority violation [trace_id={trace_id}]: {violation.detail}")
            return False, violation
        
        self.successful_crossings += 1
        self.logger.info(f"Governance decision validated [trace_id={trace_id}] — forwarding to ENFORCEMENT")
        
        return True, rajya_decision
    
    def get_stats(self) -> Dict:
        return {
            "adapter": "rajya_to_enforcement",
            "successful_crossings": self.successful_crossings,
            "violations": len(self.violation_log),
            "violation_details": self.violation_log
        }


class ExecutionToBucketAdapter:
    
    
    def __init__(self):
        self.logger = logging.getLogger("adapter-execution-to-bucket")
        self.violation_log = []
        self.successful_writes = 0
        self.events_stored = []
        
    def validate_and_write(self, event_record: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | ContractViolation]:
        
        trace_id = event_record.get("trace_id", "UNKNOWN")
        
        valid, msg = EventRecordContract.validate(event_record)
        if not valid:
            violation = ContractViolation(
                adapter="execution_to_bucket",
                violation_type="contract_validation",
                detail=msg,
                trace_id=trace_id
            )
            self.violation_log.append(asdict(violation))
            self.logger.error(f"Contract violation [trace_id={trace_id}]: {msg}")
            return False, violation
        
        
        event_with_bucket_metadata = {
            **event_record,
            "bucket_write_timestamp": datetime.utcnow().isoformat() + "Z",
            "bucket_write_index": self.successful_writes,
            "bucket_sealed": True  # Immutable after write
        }
        
        self.events_stored.append(event_with_bucket_metadata)
        self.successful_writes += 1
        
        self.logger.info(f"Event written to Bucket [trace_id={trace_id}] — index={self.successful_writes}")
        
        return True, event_with_bucket_metadata
    
    def read_event(self, trace_id: str) -> Dict[str, Any] | None:
       
        for event in self.events_stored:
            if event.get("trace_id") == trace_id:
                self.logger.info(f"Event retrieved from Bucket [trace_id={trace_id}]")
                return event
        self.logger.warning(f"Event not found in Bucket [trace_id={trace_id}]")
        return None
    
    def get_stats(self) -> Dict:
        return {
            "adapter": "execution_to_bucket",
            "successful_writes": self.successful_writes,
            "events_stored": len(self.events_stored),
            "violations": len(self.violation_log),
            "violation_details": self.violation_log
        }


class BucketToInsightBridgeAdapter:
    
    
    def __init__(self):
        self.logger = logging.getLogger("adapter-bucket-to-insightbridge")
        self.metrics_emitted = 0
        self.telemetry_records = []
        
    def emit_telemetry(self, event_record: Dict[str, Any]) -> Dict[str, Any]:
        
        trace_id = event_record.get("trace_id", "UNKNOWN")
        
        telemetry = {
            "trace_id": trace_id,
            "metric_type": "execution_event",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_stage": event_record.get("event_data", {}).get("stage", "unknown"),
            "event_outcome": event_record.get("event_data", {}).get("outcome", "unknown"),
            "execution_time_ms": event_record.get("event_data", {}).get("execution_time_ms", 0),
            "source": "bucket"
        }
        
        self.telemetry_records.append(telemetry)
        self.metrics_emitted += 1
        
        self.logger.info(f"Telemetry emitted [trace_id={trace_id}] — total={self.metrics_emitted}")
        
        return telemetry
    
    def query_metrics(self, trace_id: str) -> List[Dict[str, Any]]:
        
        results = [t for t in self.telemetry_records if t.get("trace_id") == trace_id]
        self.logger.info(f"Metrics query [trace_id={trace_id}] — results={len(results)}")
        return results
    
    def get_stats(self) -> Dict:
        return {
            "adapter": "bucket_to_insightbridge",
            "metrics_emitted": self.metrics_emitted,
            "telemetry_records": len(self.telemetry_records)
        }


class AdapterChain:
   
    
    def __init__(self):
        self.logger = logging.getLogger("adapter-chain")
        self.sanskar_to_rajya = SanskariToRajyaAdapter()
        self.rajya_to_enforcement = RajyaToEnforcementAdapter()
        self.execution_to_bucket = ExecutionToBucketAdapter()
        self.bucket_to_insightbridge = BucketToInsightBridgeAdapter()
        self.trace_index = {}  # trace_id → full execution trace
        
    def process_sanskar_output(self, sanskar_output: Dict[str, Any]) -> Tuple[bool, Dict]:
        
        trace_id = sanskar_output.get("trace_id", "UNKNOWN")
        
        
        valid, result = self.sanskar_to_rajya.validate_and_forward(sanskar_output)
        if not valid:
            self.logger.error(f"SANSKAR output rejected [trace_id={trace_id}]")
            return False, result
        
        
        if trace_id not in self.trace_index:
            self.trace_index[trace_id] = {
                "trace_id": trace_id,
                "stages": []
            }
        self.trace_index[trace_id]["stages"].append({
            "stage": "sanskar",
            "output": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        return True, result
    
    def record_governance_decision(self, rajya_decision: Dict[str, Any]) -> Tuple[bool, Dict]:
        
        trace_id = rajya_decision.get("trace_id", "UNKNOWN")
        
        valid, result = self.rajya_to_enforcement.validate_and_forward(rajya_decision)
        if not valid:
            self.logger.error(f"RAJYA decision rejected [trace_id={trace_id}]")
            return False, result
        
       
        if trace_id in self.trace_index:
            self.trace_index[trace_id]["stages"].append({
                "stage": "rajya",
                "output": result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        return True, result
    
    def record_execution_event(self, event_record: Dict[str, Any]) -> Tuple[bool, Dict]:
        
        trace_id = event_record.get("trace_id", "UNKNOWN")
        
        
        valid, bucket_result = self.execution_to_bucket.validate_and_write(event_record)
        if not valid:
            self.logger.error(f"Execution event rejected [trace_id={trace_id}]")
            return False, bucket_result
        
        
        self.bucket_to_insightbridge.emit_telemetry(bucket_result)
        
        
        if trace_id in self.trace_index:
            self.trace_index[trace_id]["stages"].append({
                "stage": "execution",
                "output": bucket_result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        return True, bucket_result
    
    def get_trace(self, trace_id: str) -> Dict | None:
        
        return self.trace_index.get(trace_id)
    
    def get_all_stats(self) -> Dict:
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trace_count": len(self.trace_index),
            "adapters": {
                "sanskar_to_rajya": self.sanskar_to_rajya.get_stats(),
                "rajya_to_enforcement": self.rajya_to_enforcement.get_stats(),
                "execution_to_bucket": self.execution_to_bucket.get_stats(),
                "bucket_to_insightbridge": self.bucket_to_insightbridge.get_stats()
            }
        }


if __name__ == "__main__":
    
    print("Runtime Adapters — Phase 2 Contract Enforcement")
    print("=" * 60)
    
    chain = AdapterChain()
    
    
    valid_sanskar_output = {
        "trace_id": "trace-test001",
        "stage": "sanskar",
        "entities": [
            {
                "entity_id": "region_a",
                "score": 0.85,
                "confidence": 0.92,
                "decision_state": "CONFIDENT",
                "reasoning": "High yield potential"
            }
        ],
        "ranking": ["region_a"],
        "metadata": {
            "schema_version": "v1",
            "algorithm": "max_yield_selector",
            "execution_time_ms": 2.5,
            "owner": "sanskar"
        }
    }
    
    success, result = chain.process_sanskar_output(valid_sanskar_output)
    print(f"\n✓ Valid SANSKAR output: {success}")
    print(f"  Contract version: {result.get('contract_version')}")
    
   
    invalid_sanskar_output = {
        "stage": "sanskar",
        "entities": [],
        "ranking": [],
        "metadata": {}
    }
    
    success, result = chain.process_sanskar_output(invalid_sanskar_output)
    print(f"\n✗ Invalid SANSKAR output (no trace_id): {success}")
    if isinstance(result, ContractViolation):
        print(f"  Violation: {result.violation_type} — {result.detail}")
    
    
    unauthorized_output = {
        "trace_id": "trace-test002",
        "stage": "sanskar",
        "entities": [],
        "ranking": [],
        "metadata": {},
        "governance_decision": "REJECTED"  # ← FORBIDDEN
    }
    
    success, result = chain.process_sanskar_output(unauthorized_output)
    print(f"\n✗ SANSKAR authority violation: {success}")
    if isinstance(result, ContractViolation):
        print(f"  Violation: {result.violation_type} — {result.detail}")
    
    
    print("\n" + "=" * 60)
    print("Adapter Statistics:")
    import pprint
    pprint.pprint(chain.get_all_stats())
