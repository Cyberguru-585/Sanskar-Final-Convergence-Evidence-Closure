

import json
from typing import Dict, Any


class StageService:
    """Base class for pipeline stages as isolated services."""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
    
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclass to validate stage input."""
        raise NotImplementedError
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclass to execute stage logic."""
        raise NotImplementedError
    
    def execute_isolated(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stage with isolation guarantees."""
        try:
            validated = self.validate_input(input_data)
            result = self.execute(validated)
            return result
        except Exception as e:
            return {
                "trace_id": input_data.get("trace_id", "UNKNOWN"),
                "stage": self.stage_name,
                "failure": {
                    "stage": self.stage_name,
                    "code": "EXECUTION_ERROR",
                    "message": str(e),
                    "trace_preserved": True
                },
                "contract_version": "v1"
            }


class SanskaarStageService(StageService):
    """Sanskar stage as isolated service."""
    
    def __init__(self):
        super().__init__("sanskar")
    
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Sanskar input contract."""
        required_fields = ["trace_id", "signal"]
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
        
        if "dataset" not in input_data["signal"]:
            raise ValueError("Dataset path missing in signal")
        
        return input_data
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Sanskar logic."""
        from sanskar import run_sanskar
        return run_sanskar(input_data)


class CoreStageService(StageService):
    """Core stage as isolated service."""
    
    def __init__(self):
        super().__init__("core")
    
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Core input contract."""
        required_fields = ["trace_id", "stage", "entities", "ranking"]
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
        
        return input_data
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Core logic."""
        from core import run_core
        return run_core(input_data)


class EnforcementStageService(StageService):
    """Enforcement stage as isolated service."""
    
    def __init__(self):
        super().__init__("enforcement")
    
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Enforcement input contract."""
        required_fields = ["trace_id", "stage", "selected_entity", "priority"]
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
        
        return input_data
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Enforcement logic."""
        from enforcement import run_enforcement
        return run_enforcement(input_data)


class DistributedServiceRegistry:
    """Registry for accessing pipeline stages as services."""
    
    def __init__(self):
        self.services = {
            "sanskar": SanskaarStageService(),
            "core": CoreStageService(),
            "enforcement": EnforcementStageService()
        }
    
    def get_service(self, stage_name: str) -> StageService:
        """Get stage service by name."""
        if stage_name not in self.services:
            raise ValueError(f"Unknown stage: {stage_name}")
        return self.services[stage_name]
    
    def call_stage(self, stage_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call stage service with input isolation."""
        service = self.get_service(stage_name)
        return service.execute_isolated(input_data)
    
    def list_services(self) -> list:
        """List available services."""
        return list(self.services.keys())



_registry = None

def get_service_registry() -> DistributedServiceRegistry:
    """Get or create global service registry."""
    global _registry
    if _registry is None:
        _registry = DistributedServiceRegistry()
    return _registry
