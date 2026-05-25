

import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
import uuid


class ContractSchema(Enum):
    
    V1 = "v1"
    V1_1 = "v1.1"


class IntegrationParticipant(Enum):
    
    SIGNAL_SOURCE = "signal_source"
    SANSKAR = "sanskar"
    RAJYA = "rajya"
    BUCKET = "bucket"
    INSIGHT_BRIDGE = "insight_bridge"
    ENFORCEMENT = "enforcement"


class TraceProperty:
    
    
    @staticmethod
    def validate_trace_id(trace_id: str) -> bool:
        
        return trace_id.startswith("TRACE-") and len(trace_id) > 6
    
    @staticmethod
    def propagate_trace(source_contract: Dict, target_contract: Dict) -> Dict:
        
        if "trace_id" not in source_contract:
            raise ValueError("Source contract missing trace_id")
        
        target_contract["trace_id"] = source_contract["trace_id"]
        target_contract["upstream_trace_id"] = source_contract.get("trace_id")
        return target_contract
    
    @staticmethod
    def verify_trace_survival(contracts: List[Dict], trace_id: str) -> Dict:
        
        result = {
            "expected_trace_id": trace_id,
            "stages_validated": 0,
            "trace_preserved": True,
            "divergences": []
        }
        
        for stage_name, contract in contracts:
            if "trace_id" in contract:
                if contract["trace_id"] == trace_id:
                    result["stages_validated"] += 1
                else:
                    result["trace_preserved"] = False
                    result["divergences"].append({
                        "stage": stage_name,
                        "expected": trace_id,
                        "found": contract["trace_id"],
                        "status": "DIVERGED"
                    })
        
        result["verdict"] = "PASS" if result["trace_preserved"] else "FAIL"
        return result


class SchemaValidator:
    
    
    INPUT_SIGNAL_SCHEMA = {
        "required_fields": ["trace_id", "signal", "timestamp"],
        "field_types": {
            "trace_id": str,
            "signal": dict,
            "timestamp": str,
            "contract_version": str
        },
        "contract_version": "v1"
    }
    
    SANSKAR_OUTPUT_SCHEMA = {
        "required_fields": ["trace_id", "entities", "ranking", "confidence", "decision_state"],
        "field_types": {
            "trace_id": str,
            "entities": list,
            "ranking": list,
            "confidence": (int, float),
            "decision_state": str,
            "contract_version": str
        },
        "contract_version": "v1"
    }
    
    RAJYA_VALIDATION_SCHEMA = {
        "required_fields": ["trace_id", "validation_status", "legitimacy_verdict", "governance_constraint"],
        "field_types": {
            "trace_id": str,
            "validation_status": str,
            "legitimacy_verdict": str,
            "governance_constraint": dict,
            "contract_version": str
        },
        "contract_version": "v1"
    }
    
    BUCKET_PERSISTENCE_SCHEMA = {
        "required_fields": ["trace_id", "stage", "execution_hash", "immutable_timestamp"],
        "field_types": {
            "trace_id": str,
            "stage": str,
            "execution_hash": str,
            "immutable_timestamp": str,
            "contract_version": str
        },
        "contract_version": "v1"
    }
    
    TELEMETRY_SCHEMA = {
        "required_fields": ["trace_id", "stage", "telemetry_data"],
        "field_types": {
            "trace_id": str,
            "stage": str,
            "telemetry_data": dict,
            "contract_version": str
        },
        "contract_version": "v1"
    }
    
    @staticmethod
    def validate(contract: Dict, schema: Dict) -> Tuple[bool, List[str]]:
        
        errors = []
        
        
        for field in schema.get("required_fields", []):
            if field not in contract:
                errors.append(f"Missing required field: {field}")
        
        
        for field, expected_type in schema.get("field_types", {}).items():
            if field in contract:
                value = contract[field]
                if not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' has type {type(value).__name__}, expected {expected_type}")
        
        return len(errors) == 0, errors


class ContractExchange:
    
    
    def __init__(self):
        self.exchanges = []
        self.trace_log = {}
    
    def compute_contract_hash(self, contract: Dict) -> str:
        
        serialized = json.dumps(contract, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    def signal_source_to_sanskar(self, 
                                 signal_data: Dict,
                                 trace_id: str = None) -> Tuple[Dict, Dict]:
        
        if not trace_id:
            trace_id = f"TRACE-{uuid.uuid4().hex[:12]}"
        
        
        input_contract = {
            "trace_id": trace_id,
            "signal": signal_data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "contract_version": ContractSchema.V1.value,
            "producer": IntegrationParticipant.SIGNAL_SOURCE.value
        }
        
        
        is_valid, errors = SchemaValidator.validate(input_contract, SchemaValidator.INPUT_SIGNAL_SCHEMA)
        if not is_valid:
            return input_contract, {"error": errors, "trace_id": trace_id, "status": "VALIDATION_FAILED"}
        
        
        sanskar_output = {
            "trace_id": trace_id,  
            "stage": IntegrationParticipant.SANSKAR.value,
            "entities": signal_data.get("entities", []),
            "ranking": signal_data.get("ranking", []),
            "confidence": signal_data.get("confidence", 0.8),
            "decision_state": signal_data.get("decision_state", "CONFIDENT"),
            "contract_version": ContractSchema.V1.value,
            "execution_hash": self.compute_contract_hash(input_contract),
            "producer": IntegrationParticipant.SANSKAR.value
        }
        
        
        is_valid, errors = SchemaValidator.validate(sanskar_output, SchemaValidator.SANSKAR_OUTPUT_SCHEMA)
        if not is_valid:
            sanskar_output["validation_error"] = errors
        
        
        exchange_record = {
            "trace_id": trace_id,
            "exchange": "signal_source → sanskar",
            "input_hash": self.compute_contract_hash(input_contract),
            "output_hash": self.compute_contract_hash(sanskar_output),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.exchanges.append(exchange_record)
        self.trace_log[trace_id] = [
            ("signal_source", input_contract),
            ("sanskar", sanskar_output)
        ]
        
        return input_contract, sanskar_output
    
    def sanskar_to_rajya(self, 
                         sanskar_output: Dict) -> Tuple[Dict, Dict]:
        
        trace_id = sanskar_output["trace_id"]
        
        
        rajya_validation = {
            "trace_id": trace_id,  
            "stage": IntegrationParticipant.RAJYA.value,
            "input_contract_hash": self.compute_contract_hash(sanskar_output),
            "validation_status": "APPROVED" if sanskar_output.get("confidence", 0) > 0.7 else "REVIEW_REQUIRED",
            "legitimacy_verdict": "LEGITIMATE" if sanskar_output.get("decision_state") == "CONFIDENT" else "AMBIGUOUS",
            "governance_constraint": {
                "confidence_not_legitimacy": True,
                "intelligence_not_governance": True,
                "boundary_respected": True
            },
            "contract_version": ContractSchema.V1.value,
            "producer": IntegrationParticipant.RAJYA.value
        }
        
        
        is_valid, errors = SchemaValidator.validate(rajya_validation, SchemaValidator.RAJYA_VALIDATION_SCHEMA)
        if not is_valid:
            rajya_validation["validation_error"] = errors
        
        
        exchange_record = {
            "trace_id": trace_id,
            "exchange": "sanskar → rajya",
            "input_hash": self.compute_contract_hash(sanskar_output),
            "output_hash": self.compute_contract_hash(rajya_validation),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.exchanges.append(exchange_record)
        
        if trace_id in self.trace_log:
            self.trace_log[trace_id].append(("rajya", rajya_validation))
        
        return sanskar_output, rajya_validation
    
    def rajya_to_enforcement(self, rajya_validation: Dict) -> Tuple[Dict, Dict]:
        
        trace_id = rajya_validation["trace_id"]
        
        enforcement_directive = {
            "trace_id": trace_id,  # PRESERVED
            "stage": IntegrationParticipant.ENFORCEMENT.value,
            "directive_source": IntegrationParticipant.RAJYA.value,
            "approval_status": rajya_validation["validation_status"],
            "legitimacy": rajya_validation["legitimacy_verdict"],
            "execution_directives": [
                {"action": "EXECUTE", "authorized": True} if rajya_validation["validation_status"] == "APPROVED" else {"action": "BLOCK", "reason": "RAJYA_REVIEW_REQUIRED"}
            ],
            "contract_version": ContractSchema.V1.value,
            "producer": IntegrationParticipant.ENFORCEMENT.value
        }
        
        
        exchange_record = {
            "trace_id": trace_id,
            "exchange": "rajya → enforcement",
            "input_hash": self.compute_contract_hash(rajya_validation),
            "output_hash": self.compute_contract_hash(enforcement_directive),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.exchanges.append(exchange_record)
        
        if trace_id in self.trace_log:
            self.trace_log[trace_id].append(("enforcement", enforcement_directive))
        
        return rajya_validation, enforcement_directive
    
    def any_stage_to_bucket(self, 
                            stage_output: Dict,
                            stage_name: str) -> Dict:
        
        trace_id = stage_output["trace_id"]
        
        bucket_persistence = {
            "trace_id": trace_id,  # PRESERVED
            "stage": stage_name,
            "execution_hash": self.compute_contract_hash(stage_output),
            "immutable_timestamp": datetime.utcnow().isoformat() + "Z",
            "storage_location": f"bucket://traces/{trace_id}/{stage_name}",
            "lineage_position": len(self.trace_log.get(trace_id, [])),
            "contract_version": ContractSchema.V1.value,
            "producer": IntegrationParticipant.BUCKET.value
        }
        
        
        is_valid, errors = SchemaValidator.validate(bucket_persistence, SchemaValidator.BUCKET_PERSISTENCE_SCHEMA)
        if not is_valid:
            bucket_persistence["validation_error"] = errors
        
        
        exchange_record = {
            "trace_id": trace_id,
            "exchange": f"{stage_name} → bucket",
            "input_hash": self.compute_contract_hash(stage_output),
            "output_hash": self.compute_contract_hash(bucket_persistence),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.exchanges.append(exchange_record)
        
        return bucket_persistence
    
    def any_stage_to_insight_bridge(self,
                                     stage_output: Dict,
                                     stage_name: str) -> Dict:
        
        trace_id = stage_output["trace_id"]
        
        telemetry = {
            "trace_id": trace_id,  # PRESERVED
            "stage": stage_name,
            "telemetry_data": {
                "execution_time_ms": 10,
                "input_size_bytes": len(json.dumps(stage_output)),
                "output_hash": self.compute_contract_hash(stage_output),
                "stage_status": "SUCCESS"
            },
            "contract_version": ContractSchema.V1.value,
            "producer": IntegrationParticipant.INSIGHT_BRIDGE.value
        }
        
        
        is_valid, errors = SchemaValidator.validate(telemetry, SchemaValidator.TELEMETRY_SCHEMA)
        if not is_valid:
            telemetry["validation_error"] = errors
        
        return telemetry
    
    def get_trace_continuity_proof(self, trace_id: str) -> Dict:
        
        if trace_id not in self.trace_log:
            return {"error": f"Trace {trace_id} not found"}
        
        return TraceProperty.verify_trace_survival(self.trace_log[trace_id], trace_id)
    
    def get_exchange_report(self) -> Dict:
        
        return {
            "total_exchanges": len(self.exchanges),
            "traces_processed": len(self.trace_log),
            "exchanges": self.exchanges,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def run_live_integration_chain(signal_data: Dict, trace_id: str = None) -> Dict:
    
    exchange = ContractExchange()
    
    
    input_contract, sanskar_output = exchange.signal_source_to_sanskar(signal_data, trace_id)
    if "error" in sanskar_output:
        return {"error": sanskar_output, "status": "FAILED_AT_SIGNAL_SOURCE"}
    
    trace_id = sanskar_output["trace_id"]
    
    
    sanskar_output_copy, rajya_validation = exchange.sanskar_to_rajya(sanskar_output)
    exchange.any_stage_to_bucket(sanskar_output, "sanskar")
    exchange.any_stage_to_insight_bridge(sanskar_output, "sanskar")
    
    
    rajya_output, enforcement_directive = exchange.rajya_to_enforcement(rajya_validation)
    exchange.any_stage_to_bucket(rajya_validation, "rajya")
    exchange.any_stage_to_insight_bridge(rajya_validation, "rajya")
    
    
    exchange.any_stage_to_bucket(enforcement_directive, "enforcement")
    exchange.any_stage_to_insight_bridge(enforcement_directive, "enforcement")
    
    
    trace_proof = exchange.get_trace_continuity_proof(trace_id)
    
    
    result = {
        "trace_id": trace_id,
        "pipeline_status": "SUCCESS",
        "stages_completed": 4,
        "stage_outputs": {
            "signal_source": input_contract,
            "sanskar": sanskar_output,
            "rajya": rajya_validation,
            "enforcement": enforcement_directive
        },
        "trace_continuity_proof": trace_proof,
        "contract_exchanges": exchange.get_exchange_report(),
        "execution_timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return result


if __name__ == "__main__":
    
    test_signal = {
        "entities": [
            {"entity_id": "ENTITY-1", "score": 0.95},
            {"entity_id": "ENTITY-2", "score": 0.85}
        ],
        "ranking": ["ENTITY-1", "ENTITY-2"],
        "confidence": 0.92,
        "decision_state": "CONFIDENT"
    }
    
    result = run_live_integration_chain(test_signal)
    print(json.dumps(result, indent=2))
