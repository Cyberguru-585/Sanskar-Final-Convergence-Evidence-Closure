# TRACE_SCHEMA_PROVENANCE.md — Phase 3: Metadata & Continuity

**Date:** June 3, 2026  
**Status:** INTEGRATION PHASE 3 — Trace, Schema, and Provenance  
**Scope:** Full execution chain with metadata tracking  

---

## 1. TRACE CONTINUITY SPECIFICATION

### Trace Identity

Every request has a **single, immutable trace_id** that flows through all stages.

```
Signal Input [trace_id generated or provided]
  ↓ [trace_id preserved]
SANSKAR [trace_id required, must match input]
  ↓ [trace_id in output]
RAJYA [receives SANSKAR's trace_id]
  ↓ [trace_id in governance decision]
ENFORCEMENT [receives RAJYA's trace_id]
  ↓ [trace_id in enforcement directive]
Execution [receives directive's trace_id]
  ↓ [trace_id in execution result]
Bucket [records with trace_id as primary key]
  ↓ [trace_id in event record]
InsightBridge [metrics tagged with trace_id]
```

### Trace_ID Format

```
trace_id: "trace-" + hex(8-character segment)
Example: trace-7af92126
```

**Properties:**
- Immutable after creation
- Globally unique per request
- Used as primary key in event store
- Enables deterministic replay

### Trace Verification Algorithm

```python
def verify_trace_continuity(stages: List[Tuple[str, Dict]]) -> bool:
    """All stages must have identical trace_id."""
    expected_trace_id = stages[0][1]["trace_id"]
    
    for stage_name, stage_output in stages:
        if stage_output.get("trace_id") != expected_trace_id:
            raise TraceDiscontinuityError(
                f"Stage {stage_name} has different trace_id: "
                f"expected {expected_trace_id}, "
                f"got {stage_output.get('trace_id')}"
            )
    
    return True
```

### Trace Break Detection

A trace break occurs when:
1. trace_id changes mid-chain
2. trace_id is dropped at a stage
3. trace_id is corrupted
4. trace_id cannot be recovered from event store

**Detection:** Authority Detector monitors all outputs for trace breaks.

---

## 2. SCHEMA VERSIONING

### Schema Evolution Policy

All contracts must declare `schema_version` and `contract_version`.

**Versioning Rules:**

1. **Major version** (v1 → v2): Breaking changes, old versions not accepted
2. **Minor version** (v1.0 → v1.1): Backward-compatible additions
3. **Patch version** (v1.0 → v1.0.1): Bug fixes only

### Active Schemas

#### Intelligence Output Schema v1

```json
{
  "schema_version": "v1",
  "contract_version": "intelligence_output_v1",
  "owner": "sanskar",
  "updated": "2026-06-03",
  "fields": {
    "trace_id": {
      "type": "string",
      "description": "Immutable request identifier",
      "required": true,
      "example": "trace-7af92126"
    },
    "stage": {
      "type": "string",
      "enum": ["sanskar"],
      "required": true,
      "description": "Must be 'sanskar'"
    },
    "entities": {
      "type": "array of objects",
      "required": true,
      "description": "Ranked candidates with scores",
      "items": {
        "entity_id": "string (required)",
        "score": "float in [0.0, 1.0] (required)",
        "confidence": "float in [0.0, 1.0] (required)",
        "decision_state": "CONFIDENT|AMBIGUOUS|LOW_CONFIDENCE (required)",
        "reasoning": "string (optional)"
      }
    },
    "ranking": {
      "type": "array of strings",
      "required": true,
      "description": "Ordered list of entity_ids from highest to lowest score"
    },
    "metadata": {
      "type": "object",
      "required": true,
      "fields": {
        "schema_version": "string (e.g., 'v1')",
        "algorithm": "string (algorithm name)",
        "execution_time_ms": "float",
        "owner": "string ('sanskar')"
      }
    }
  }
}
```

#### Governance Decision Schema v1

```json
{
  "schema_version": "v1",
  "contract_version": "governance_decision_v1",
  "owner": "rajya",
  "updated": "2026-06-03",
  "fields": {
    "trace_id": {
      "type": "string",
      "required": true,
      "description": "Must match SANSKAR output's trace_id"
    },
    "stage": {
      "type": "string",
      "enum": ["rajya"],
      "required": true
    },
    "decision": {
      "type": "string",
      "enum": ["APPROVED", "REJECTED", "DEFERRED"],
      "required": true,
      "description": "Governance decision on SANSKAR's recommendation"
    },
    "selected_entity": {
      "type": "string",
      "required": false,
      "description": "Entity selected by RAJYA (may differ from SANSKAR's top rank)"
    },
    "override_reason": {
      "type": "string",
      "required": false,
      "description": "Reason for override if decision != APPROVED"
    },
    "authority_check": {
      "type": "object",
      "required": true,
      "fields": {
        "decision_maker": "string ('rajya')",
        "constitutional_authority": "boolean (must be true)",
        "sign_off_timestamp": "ISO8601"
      }
    }
  }
}
```

#### Event Record Schema v1

```json
{
  "schema_version": "v1",
  "contract_version": "event_record_v1",
  "owner": "bucket",
  "updated": "2026-06-03",
  "fields": {
    "trace_id": {
      "type": "string",
      "required": true,
      "description": "Primary key in event store"
    },
    "event_type": {
      "type": "string",
      "enum": ["execution_complete", "failure", "partial_execution"],
      "required": true
    },
    "event_data": {
      "type": "object",
      "required": true,
      "fields": {
        "stage": "string",
        "outcome": "SUCCESS|FAILURE|PARTIAL",
        "resource_allocated": "object",
        "execution_time_ms": "float"
      }
    },
    "ownership": {
      "type": "object",
      "required": true,
      "fields": {
        "owner": "string ('bucket')",
        "immutable": "boolean (true)",
        "signed": "boolean"
      }
    }
  }
}
```

### Schema Compatibility Check

```python
def validate_schema_compatibility(data: Dict, required_schema_version: str) -> bool:
    """
    Ensure data conforms to required schema version.
    
    For v1 → v1.1: Accept (backward compatible)
    For v1.1 → v1: Reject (missing optional fields)
    For v1 → v2: Reject (breaking change)
    """
    declared_version = data.get("schema_version", "unknown")
    
    if declared_version == required_schema_version:
        return True
    
    # Backward compatibility: old data accepted by newer systems
    if is_backward_compatible(declared_version, required_schema_version):
        return True
    
    return False
```

---

## 3. OWNERSHIP METADATA

### Ownership Declaration

Every output must declare its owner.

```json
{
  "trace_id": "trace-7af92126",
  "stage": "sanskar",
  "owner": "sanskar",
  "ownership_proof": {
    "producer": "sanskar",
    "producer_version": "2.1.0",
    "producer_timestamp": "2026-06-03T12:00:00Z",
    "can_be_modified_by": [],
    "can_be_read_by": ["rajya", "enforcement", "bucket", "insightbridge"],
    "immutability_level": "IMMUTABLE_AFTER_HANDOFF"
  }
}
```

### Ownership Transfer Rules

```
SANSKAR produces: ownership_proof.producer = "sanskar"
  ↓ [handoff to RAJYA]
RAJYA receives: ownership_proof.producer = "sanskar" (original producer)
               ownership_proof.current_owner = "rajya" (new owner)
  ↓ [handoff to ENFORCEMENT]
ENFORCEMENT receives: original producer retained, current owner = "enforcement"
  ↓ [handoff to Bucket]
Bucket stores: all ownership lineage preserved
```

### Authority Mismatch Detection

```python
def detect_authority_mismatch(output: Dict) -> bool:
    """
    Detect if output's declared owner matches actual producer.
    
    Violation example:
    - SANSKAR claims to own "governance_decision" (forbidden)
    - ENFORCEMENT claims to own "intelligence_ranking" (forbidden)
    """
    producer = output.get("metadata", {}).get("owner")
    forbidden_outputs = {
        "sanskar": {"enforcement_directive", "governance_decision", "bucket_write_direct"},
        "enforcement": {"intelligence_signal", "ranking", "confidence_score"},
        "rajya": {"enforcement_directive"},
        "bucket": {"observability_signal"}
    }
    
    if producer in forbidden_outputs:
        forbidden = forbidden_outputs[producer]
        actual_outputs = set(output.keys())
        violations = forbidden & actual_outputs
        
        if violations:
            return True  # Mismatch detected
    
    return False
```

---

## 4. COMPATIBILITY METADATA

### Compatibility Assertion

Each output must assert compatibility with downstream systems.

```json
{
  "trace_id": "trace-7af92126",
  "stage": "sanskar",
  "compatibility": {
    "requires_rajya_version": ">=1.0.0",
    "requires_enforcement_version": ">=1.5.0",
    "requires_bucket_version": ">=2.0.0",
    "requires_insightbridge_version": ">=1.2.0",
    "deprecated_after": null,
    "compatibility_check_timestamp": "2026-06-03T12:00:00Z",
    "is_compatible": true
  }
}
```

### Compatibility Verification

```python
def verify_compatibility(output: Dict, downstream_system_versions: Dict) -> bool:
    """
    Verify output is compatible with all downstream systems.
    
    Returns: True if compatible with all downstream systems
    Raises: CompatibilityError if any version mismatch
    """
    compat = output.get("compatibility", {})
    
    checks = {
        "rajya": "requires_rajya_version",
        "enforcement": "requires_enforcement_version",
        "bucket": "requires_bucket_version",
        "insightbridge": "requires_insightbridge_version"
    }
    
    for system, version_field in checks.items():
        required = compat.get(version_field)
        actual = downstream_system_versions.get(system)
        
        if not version_satisfies(actual, required):
            raise CompatibilityError(
                f"{system}: required {required}, have {actual}"
            )
    
    return True
```

---

## 5. PROVENANCE METADATA

### Full Execution Provenance

```json
{
  "trace_id": "trace-7af92126",
  "provenance": {
    "signal_source": "weather_api",
    "signal_timestamp": "2026-06-03T11:50:00Z",
    "signal_version": "v2.1",
    "sanskar_version": "2.1.0",
    "sanskar_algorithm": "max_yield_selector",
    "sanskar_start_time": "2026-06-03T11:50:01.000Z",
    "sanskar_end_time": "2026-06-03T11:50:01.002Z",
    "sanskar_execution_time_ms": 2.0,
    "rajya_version": "1.5.2",
    "rajya_received_time": "2026-06-03T11:50:01.003Z",
    "rajya_decision_time": "2026-06-03T11:50:01.050Z",
    "enforcement_version": "1.2.1",
    "enforcement_received_time": "2026-06-03T11:50:01.051Z",
    "enforcement_directive_count": 3,
    "execution_start_time": "2026-06-03T11:50:01.052Z",
    "execution_end_time": "2026-06-03T11:50:01.200Z",
    "bucket_write_time": "2026-06-03T11:50:01.201Z",
    "bucket_event_index": 1042,
    "insightbridge_metric_timestamp": "2026-06-03T11:50:01.202Z",
    "total_latency_ms": 202.0
  }
}
```

### Provenance Chain

```python
def build_provenance_chain(trace_id: str) -> Dict:
    """
    Reconstruct full execution provenance from event store.
    
    Returns:
    {
        "trace_id": trace_id,
        "signal": {input signal with timestamp, version, source},
        "sanskar": {execution data, timing, algorithm, version},
        "rajya": {decision, timing, version},
        "enforcement": {directives, count, timing, version},
        "execution": {resources, outcome, timing},
        "bucket": {write timestamp, index, immutability proof},
        "insightbridge": {metrics, timestamp},
        "total_latency_ms": computed end-to-end time
    }
    """
```

---

## 6. REPLAY POSTURE

### Deterministic Replay Guarantee

Same input → identical output (guaranteed).

```json
{
  "trace_id": "trace-7af92126",
  "replay_posture": {
    "is_deterministic": true,
    "determinism_guarantee": "input_hash_identical → output_hash_identical",
    "can_be_replayed": true,
    "replay_dependencies": ["bucket", "insightbridge"],
    "replay_instruction": "Pass input + trace_id to SANSKAR. Compare output hash.",
    "input_hash": "sha256(trace-7af92126 + signal_data)",
    "output_hash": "sha256(entities + ranking + metadata)",
    "hash_algorithm": "sha256"
  }
}
```

### Replay Verification

```python
def verify_replay(trace_id: str, original_input: Dict) -> Dict:
    """
    Re-execute SANSKAR with original input.
    Compare output hashes.
    
    Returns:
    {
        "trace_id": trace_id,
        "original_output_hash": "...",
        "replayed_output_hash": "...",
        "hashes_match": true/false,
        "is_deterministic": true/false,
        "divergence_detected": false/true,
        "divergence_details": null or {...}
    }
    """
```

---

## 7. FULL-CHAIN EXAMPLE

### Example Trace: Request trace-7af92126

#### Stage 1: Signal Input

```json
{
  "trace_id": "trace-7af92126",
  "signal": {
    "regions": [
      {"name": "region_a", "yield_potential": 0.85},
      {"name": "region_b", "yield_potential": 0.72}
    ],
    "rainfall": {"amount": 45.2, "confidence": 0.88},
    "soil": {"type": "loamy", "moisture": 0.65}
  },
  "metadata": {
    "schema_version": "v1",
    "timestamp": "2026-06-03T11:50:00Z",
    "provenance": "weather_api_v2.1",
    "source": "meteorological_service"
  }
}
```

#### Stage 2: SANSKAR Output (Intelligence)

```json
{
  "trace_id": "trace-7af92126",
  "stage": "sanskar",
  "entities": [
    {
      "entity_id": "region_a",
      "score": 0.85,
      "confidence": 0.92,
      "decision_state": "CONFIDENT",
      "reasoning": "High yield potential + good moisture"
    },
    {
      "entity_id": "region_b",
      "score": 0.72,
      "confidence": 0.78,
      "decision_state": "CONFIDENT",
      "reasoning": "Moderate yield potential"
    }
  ],
  "ranking": ["region_a", "region_b"],
  "metadata": {
    "schema_version": "v1",
    "algorithm": "max_yield_selector",
    "execution_time_ms": 2.1,
    "owner": "sanskar"
  },
  "contract_version": "intelligence_output_v1",
  "ownership_proof": {
    "producer": "sanskar",
    "producer_version": "2.1.0",
    "immutability_level": "IMMUTABLE_AFTER_HANDOFF",
    "can_be_read_by": ["rajya", "enforcement", "bucket"]
  },
  "compatibility": {
    "requires_rajya_version": ">=1.0.0",
    "is_compatible": true
  }
}
```

#### Stage 3: RAJYA Decision (Governance)

```json
{
  "trace_id": "trace-7af92126",
  "stage": "rajya",
  "decision": "APPROVED",
  "selected_entity": "region_a",
  "authority_check": {
    "decision_maker": "rajya",
    "constitutional_authority": true,
    "sign_off_timestamp": "2026-06-03T11:50:01.050Z"
  },
  "contract_version": "governance_decision_v1",
  "ownership_proof": {
    "producer": "sanskar (original)",
    "current_owner": "rajya",
    "decision_authority": "rajya"
  }
}
```

#### Stage 4: ENFORCEMENT Directive

```json
{
  "trace_id": "trace-7af92126",
  "stage": "enforcement",
  "directives": [
    {
      "directive_id": "DIR-001-region_a",
      "action": "allocate_resources",
      "target": "region_a",
      "status": "PENDING_EXECUTION"
    }
  ],
  "contract_version": "enforcement_directive_v1",
  "ownership_proof": {
    "current_owner": "enforcement",
    "enforcement_authority": "fail_closed_only"
  }
}
```

#### Stage 6: Bucket Event Record

```json
{
  "trace_id": "trace-7af92126",
  "event_type": "execution_complete",
  "event_data": {
    "stage": "execution",
    "outcome": "SUCCESS",
    "resource_allocated": {
      "water": 1200,
      "fertilizer": 250,
      "labor_hours": 4
    },
    "execution_time_ms": 148.0
  },
  "ownership": {
    "owner": "bucket",
    "immutable": true,
    "signed": true
  },
  "contract_version": "event_record_v1",
  "bucket_metadata": {
    "event_index": 1042,
    "write_timestamp": "2026-06-03T11:50:01.201Z",
    "sealed": true
  }
}
```

#### Provenance Summary

```json
{
  "trace_id": "trace-7af92126",
  "provenance": {
    "signal_timestamp": "2026-06-03T11:50:00Z",
    "sanskar_time_ms": 2.1,
    "rajya_time_ms": 49.0,
    "enforcement_time_ms": 1.0,
    "execution_time_ms": 148.0,
    "bucket_write_time_ms": 1.0,
    "total_latency_ms": 201.1,
    "stages_completed": 6,
    "no_errors": true
  }
}
```

---

## 8. COMPLETENESS MATRIX

| Component | SANSKAR Responsibility | Other System Responsibility |
|-----------|----------------------|---------------------------|
| trace_id generation | Optional (accepts if provided) | Input can provide trace_id |
| trace_id preservation | **REQUIRED** | All systems preserve |
| schema_version | Declares in output | Validated at boundary |
| contract_version | Declares in output | Validated at boundary |
| ownership declaration | **REQUIRED** | May override after receipt |
| compatibility check | **REQUIRED** | Enforcement layer validates |
| provenance tracking | Contributing data | Bucket assembles chain |
| execution timing | Records its own | Others record their own |
| immutability guarantee | None (SANSKAR output) | Bucket enforces |
| determinism guarantee | **REQUIRED** | Replay engine verifies |

---

## NEXT PHASE

**Phase 4 — Governance/Drift/Boundary:** Implement authority matrix, boundary checks, drift detection for intelligence→authority migration and other critical boundaries.

