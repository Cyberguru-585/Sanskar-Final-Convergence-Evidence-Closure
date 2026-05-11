

import json
from typing import Dict, Any, List, Tuple


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


class ContractSchema:
    """Base contract schema definition."""
    
    def __init__(self, name: str, version: str, required_fields: List[str]):
        self.name = name
        self.version = version
        self.required_fields = required_fields
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate data against schema. Returns (valid, errors)."""
        errors = []
        
        # Check version
        if "contract_version" not in data:
            errors.append(f"Missing contract_version (expected {self.version})")
        elif data["contract_version"] != self.version:
            errors.append(f"Version mismatch: got {data['contract_version']}, expected {self.version}")
        
        # Check required fields
        for field in self.required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors


class InputContractSchema(ContractSchema):
    """Schema for input contracts."""
    
    def __init__(self):
        super().__init__(
            "InputContract",
            "v1",
            ["trace_id", "signal", "contract_version"]
        )
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input contract."""
        valid, errors = super().validate(data)
        
        # Additional validation for signal
        if "signal" in data and isinstance(data["signal"], dict):
            if "dataset" not in data["signal"]:
                errors.append("Signal missing dataset path")
        
        return len(errors) == 0, errors


class SanskaarOutputSchema(ContractSchema):
    """Schema for Sanskar stage output."""
    
    def __init__(self):
        super().__init__(
            "SanskaarOutput",
            "v1",
            ["trace_id", "stage", "entities", "ranking", "contract_version"]
        )
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate Sanskar output contract."""
        valid, errors = super().validate(data)
        
        # Check if failure is present (which is also valid)
        if "failure" in data:
            errors.clear()  # Failure is a valid output
            return True, errors
        
        # Check entities have required fields
        if "entities" in data and isinstance(data["entities"], list):
            for i, entity in enumerate(data["entities"]):
                if "entity_id" not in entity:
                    errors.append(f"Entity {i} missing entity_id")
                if "score" not in entity:
                    errors.append(f"Entity {i} missing score")
                if "decision_state" not in entity:
                    errors.append(f"Entity {i} missing decision_state (UNCERTAIN_DETECTION requirement)")
        
        return len(errors) == 0, errors


class CoreOutputSchema(ContractSchema):
    """Schema for Core stage output."""
    
    def __init__(self):
        super().__init__(
            "CoreOutput",
            "v1",
            ["trace_id", "stage", "selected_entity", "decision_state", "contract_version"]
        )
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate Core output contract."""
        valid, errors = super().validate(data)
        
        # Check if failure is present
        if "failure" in data:
            errors.clear()
            return True, errors
        
        # Check decision_state values
        if "selected_decision_state" in data:
            if data["selected_decision_state"] not in ["CONFIDENT", "LOW_CONFIDENCE", "AMBIGUOUS"]:
                errors.append(f"Invalid decision_state: {data['selected_decision_state']}")
        
        return len(errors) == 0, errors


class EnforcementOutputSchema(ContractSchema):
    """Schema for Enforcement stage output."""
    
    def __init__(self):
        super().__init__(
            "EnforcementOutput",
            "v1",
            ["trace_id", "stage", "target", "acknowledgment", "contract_version"]
        )
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate Enforcement output contract."""
        valid, errors = super().validate(data)
        
        
        if "failure" in data:
            errors.clear()
            return True, errors
        
        # Check acknowledgment structure
        if "acknowledgment" in data and isinstance(data["acknowledgment"], dict):
            ack = data["acknowledgment"]
            if "acknowledged" not in ack:
                errors.append("Acknowledgment missing 'acknowledged' field")
            if "execution_status" not in ack:
                errors.append("Acknowledgment missing 'execution_status' field")
            if "ack_timestamp" not in ack:
                errors.append("Acknowledgment missing 'ack_timestamp' field")
        else:
            errors.append("Missing acknowledgment structure")
        
        return len(errors) == 0, errors


class SchemaValidator:
    """Central schema validator for all contracts."""
    
    def __init__(self):
        self.schemas = {
            "input": InputContractSchema(),
            "sanskar": SanskaarOutputSchema(),
            "core": CoreOutputSchema(),
            "enforcement": EnforcementOutputSchema()
        }
    
    def validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input contract, raise on error."""
        valid, errors = self.schemas["input"].validate(data)
        if not valid:
            return {
                "valid": False,
                "contract_type": "input",
                "errors": errors,
                "validation_result": "FAILED"
            }
        return {
            "valid": True,
            "contract_type": "input",
            "errors": [],
            "validation_result": "PASSED"
        }
    
    def validate_sanskar_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Sanskar output."""
        valid, errors = self.schemas["sanskar"].validate(data)
        return {
            "valid": valid,
            "contract_type": "sanskar",
            "errors": errors,
            "validation_result": "PASSED" if valid else "FAILED"
        }
    
    def validate_core_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Core output."""
        valid, errors = self.schemas["core"].validate(data)
        return {
            "valid": valid,
            "contract_type": "core",
            "errors": errors,
            "validation_result": "PASSED" if valid else "FAILED"
        }
    
    def validate_enforcement_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Enforcement output."""
        valid, errors = self.schemas["enforcement"].validate(data)
        return {
            "valid": valid,
            "contract_type": "enforcement",
            "errors": errors,
            "validation_result": "PASSED" if valid else "FAILED"
        }


# Global validator instance
_validator = None

def get_validator() -> SchemaValidator:
    """Get or create global schema validator."""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator
