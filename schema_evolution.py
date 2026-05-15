import json
from typing import Dict, Any, List


class SchemaVersion:
    """Represents a schema version with compatibility information."""
    
    def __init__(self, version, required_fields, optional_fields, deprecated_fields=None):
        self.version = version
        self.required_fields = set(required_fields)
        self.optional_fields = set(optional_fields)
        self.deprecated_fields = set(deprecated_fields or [])
    
    def __str__(self):
        return self.version


class SchemaRegistry:
    """
    Schema version registry with backward compatibility support.
    
    Supports:
    - v1 accepted
    - v1.1 accepted
    - Unsupported versions rejected gracefully
    - Backward compatibility verification
    """
    
    def __init__(self):
        self.schemas = {}
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register default supported schema versions."""
        
        # Version 1.0 - Base schema
        self.register_schema(SchemaVersion(
            version="v1",
            required_fields=[
                "trace_id",
                "signal",
                "entities"
            ],
            optional_fields=[
                "downstream_decision",
                "scenario_analysis"
            ],
            deprecated_fields=[]
        ))
        
        # Version 1.1 - Enhanced with correlation
        self.register_schema(SchemaVersion(
            version="v1.1",
            required_fields=[
                "trace_id",
                "signal",
                "entities"
            ],
            optional_fields=[
                "correlation_id",
                "parent_trace_id",
                "downstream_decision",
                "scenario_analysis",
                "dependency_status",
                "schema_version"
            ],
            deprecated_fields=[]
        ))
        
        # Future: v1.2 with additional governance fields
        self.register_schema(SchemaVersion(
            version="v1.2",
            required_fields=[
                "trace_id",
                "signal",
                "entities"
            ],
            optional_fields=[
                "correlation_id",
                "parent_trace_id",
                "downstream_decision",
                "scenario_analysis",
                "dependency_status",
                "schema_version",
                "governance_context",
                "uncertainty_tolerance"
            ],
            deprecated_fields=[]
        ))
    
    def register_schema(self, schema):
        """Register a new schema version."""
        self.schemas[schema.version] = schema
    
    def validate_document(self, document, schema_version=None):
        """
        Validate a document against a schema version.
        
        Args:
            document: Document to validate
            schema_version: Version to validate against (auto-detect if None)
        
        Returns:
            Validation result with issues if any
        """
        if schema_version is None:
            schema_version = document.get("schema_version", "v1")
        
        if schema_version not in self.schemas:
            return {
                "valid": False,
                "schema_version": schema_version,
                "issues": [f"Unsupported schema version: {schema_version}"],
                "supported_versions": list(self.schemas.keys()),
                "verdict": f"FAIL — unsupported version {schema_version}"
            }
        
        schema = self.schemas[schema_version]
        issues = []
        
        # Check required fields
        for field in schema.required_fields:
            if field not in document:
                issues.append(f"Missing required field: {field}")
        
        # Check for deprecated fields
        for field in schema.deprecated_fields:
            if field in document:
                issues.append(f"Deprecated field present: {field} (unsupported in {schema_version})")
        
        # Check for unknown fields
        allowed_fields = schema.required_fields | schema.optional_fields | schema.deprecated_fields
        for field in document.keys():
            if field not in allowed_fields and field != "schema_version":
                issues.append(f"Unknown field: {field} (not in schema {schema_version})")
        
        result = {
            "valid": len(issues) == 0,
            "schema_version": schema_version,
            "issues": issues,
            "supported_versions": list(self.schemas.keys()),
            "verdict": "PASS — document valid" if len(issues) == 0 else f"FAIL — {len(issues)} issue(s)"
        }
        
        return result
    
    def migrate_document(self, document, target_version):
        """
        Migrate document from one schema version to another.
        
        Args:
            document: Document to migrate
            target_version: Target schema version
        
        Returns:
            Migrated document with migration metadata
        """
        source_version = document.get("schema_version", "v1")
        
        if source_version not in self.schemas:
            return {
                "success": False,
                "reason": f"Source version {source_version} not supported",
                "original": document
            }
        
        if target_version not in self.schemas:
            return {
                "success": False,
                "reason": f"Target version {target_version} not supported",
                "original": document
            }
        
        # Create migration path
        migration_path = self._compute_migration_path(source_version, target_version)
        
        if not migration_path:
            return {
                "success": False,
                "reason": f"No migration path from {source_version} to {target_version}",
                "original": document
            }
        
        # Perform migration
        migrated = document.copy()
        migrated["schema_version"] = target_version
        
        # Add compatibility metadata
        migrated["_migration_metadata"] = {
            "source_version": source_version,
            "target_version": target_version,
            "migration_path": migration_path,
            "backward_compatible": self._is_backward_compatible(source_version, target_version)
        }
        
        # Validate migrated document
        validation = self.validate_document(migrated, target_version)
        
        return {
            "success": validation["valid"],
            "migrated": migrated,
            "validation": validation,
            "migration_path": migration_path
        }
    
    def is_backward_compatible(self, from_version, to_version):
        """Check if from_version is backward compatible with to_version."""
        return self._is_backward_compatible(from_version, to_version)
    
    def _is_backward_compatible(self, from_version, to_version):
        """
        Determine backward compatibility between versions.
        
        Compatibility rules:
        - v1 is compatible with v1.1 (v1.1 only adds optional fields)
        - v1.1 is compatible with v1.2 (v1.2 only adds optional fields)
        - Later versions should be compatible with earlier
        """
        if from_version == to_version:
            return True
        
        compatibility_map = {
            ("v1", "v1.1"): True,
            ("v1", "v1.2"): True,
            ("v1.1", "v1.2"): True,
            ("v1.1", "v1"): False,  # Downgrade not allowed
            ("v1.2", "v1"): False,
            ("v1.2", "v1.1"): False,
        }
        
        return compatibility_map.get((from_version, to_version), False)
    
    def _compute_migration_path(self, source, target):
        """Compute migration path between versions."""
        # Simple linear migration path for now
        versions = ["v1", "v1.1", "v1.2"]
        
        try:
            source_idx = versions.index(source)
            target_idx = versions.index(target)
        except ValueError:
            return None
        
        if source_idx > target_idx:
            return None  # Don't support downgrade
        
        path = versions[source_idx:target_idx + 1]
        return path
    
    def get_compatibility_matrix(self):
        """Get compatibility matrix for all registered versions."""
        versions = list(self.schemas.keys())
        matrix = {}
        
        for from_v in versions:
            matrix[from_v] = {}
            for to_v in versions:
                matrix[from_v][to_v] = self._is_backward_compatible(from_v, to_v)
        
        return matrix
    
    def get_supported_versions(self):
        """Get list of supported schema versions."""
        return {
            "supported": list(self.schemas.keys()),
            "latest": sorted(self.schemas.keys())[-1],
            "schemas": {
                version: {
                    "required": list(schema.required_fields),
                    "optional": list(schema.optional_fields),
                    "deprecated": list(schema.deprecated_fields)
                }
                for version, schema in self.schemas.items()
            }
        }


def validate_input_contract(contract):
    """Validate input contract against schema registry."""
    registry = SchemaRegistry()
    schema_version = contract.get("schema_version", "v1")
    
    validation = registry.validate_document(contract, schema_version)
    
    return {
        "contract_id": contract.get("trace_id", "UNKNOWN"),
        "schema_validation": validation,
        "is_valid": validation["valid"]
    }


def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility across versions."""
    registry = SchemaRegistry()
    
    # Create v1 document
    v1_doc = {
        "trace_id": "TRACE-001",
        "signal": "test_signal",
        "entities": [{"id": "region1", "score": 0.85}]
    }
    
    # Validate v1
    v1_validation = registry.validate_document(v1_doc, "v1")
    
    # Migrate to v1.1
    migration = registry.migrate_document(v1_doc, "v1.1")
    
    # Migrate to v1.2
    migration_v12 = registry.migrate_document(migration["migrated"], "v1.2")
    
    return {
        "v1_validation": v1_validation,
        "migration_to_v11": migration,
        "migration_to_v12": migration_v12,
        "compatibility_matrix": registry.get_compatibility_matrix()
    }
