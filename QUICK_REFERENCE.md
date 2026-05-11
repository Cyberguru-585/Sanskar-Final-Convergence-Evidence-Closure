# SANSKAR UPGRADE - QUICK REFERENCE GUIDE

##  Quick Start

### Basic Execution (Standard)
```python
from tantra import run_tantra

input_contract = {
    "trace_id": "MY-TRACE-001",
    "signal": {
        "dataset": "crop_yield.csv"
    }
}

result = run_tantra(input_contract)
print(result["truth"]["verdict"])  # "PIPELINE_COMPLETE"
```

### With Replay Mode
```python
# Execute with replay from event store
result = run_tantra(input_contract, replay_mode=True)
print(result["observability"]["stage_latencies"])
```

---

##  8 Key Features - Usage Examples

### 1. Uncertainty Detection
```python
result = run_tantra(input_contract)
entities = result["sanskar_output"]["entities"]

for entity in entities:
    print(f"{entity['entity_id']}: {entity['decision_state']}")
    # Output: North: CONFIDENT, East: LOW_CONFIDENCE, etc.
```

### 2. Confidence Factors
```python
entity = result["sanskar_output"]["entities"][0]
factors = entity["confidence_factors"]

print(f"Score contribution: {factors['score_contribution']}")
print(f"Feature quality: {factors['feature_quality']}")
print(f"Feature stability: {factors['feature_stability']}")
print(f"Missing penalty: {factors['missing_penalty']}")
print(f"Total confidence: {entity['confidence']}")
```

### 3. Comparative Explanations
```python
comp = result["sanskar_output"]["comparative_explanation"]

print(f"Summary: {comp['summary']}")
# Output: "North ranks above East due to stronger irrigation (+0.018)..."

for advantage in comp["advantages"]:
    print(f"  {advantage['factor']}: +{advantage['delta']}")
```

### 4. Event Sourcing & Replay
```python
# Original execution
result1 = run_tantra(input_contract)
hash1 = result1["truth"]["pipeline_hash"]

# Replay execution
result2 = run_tantra(input_contract, replay_mode=True)
hash2 = result2["truth"]["pipeline_hash"]

print(f"Determinism: {' PASS' if hash1 == hash2 else ' FAIL'}")
```

### 5. Enforcement Acknowledgment
```python
enforcement = result["enforcement"]

for directive in enforcement["directives"]:
    print(f"{directive['directive_id']}:")
    print(f"  Status: {directive.get('execution_status', 'PENDING')}")
    print(f"  Acknowledged: {directive.get('acknowledged', False)}")

ack = enforcement["acknowledgment"]
print(f"Overall: {ack['execution_status']} at {ack['status_updated_at']}")
```

### 6. Observability Telemetry
```python
obs = result["observability"]

print(f"Contract Version: {obs['contract_version']}")
print(f"Decision State: {obs['decision_state']}")

print("\nLatencies:")
for stage, latency in obs["stage_latencies"].items():
    print(f"  {stage}: {latency:.2f} ms")
```

### 7. Distributed Services
```python
from distributed_services import get_service_registry

registry = get_service_registry()


sanskar_result = registry.call_stage("sanskar", input_contract)


core_result = registry.call_stage("core", sanskar_result)


enforcement_result = registry.call_stage("enforcement", core_result)
```

### 8. Contract Validation
```python
from schema_validation import get_validator

validator = get_validator()

# Validate input
validation = validator.validate_input(input_contract)
if not validation["valid"]:
    print(f"Errors: {validation['errors']}")

# Validate sanskar output
validation = validator.validate_sanskar_output(sanskar_result)
print(f"Result: {validation['validation_result']}")
```

---

##  Output Structure Reference

### Top-Level Response
```python
{
    "trace_id": "TRACE-001",
    "pipeline_status": "SUCCESS",  # or "FAILED"
    "input": {...},
    "sanskar_output": {...},
    "core_decision": {...},
    "enforcement": {...},
    "truth": {...},
    "replay_mode": false,
    "event_sourced": true,
    "observability": {
        "stage_latencies": {...},
        "contract_version": "v1",
        "decision_state": "CONFIDENT"
    },
    "contract_version": "v1"
}
```

### Entity Structure
```python
{
    "entity_id": "North",
    "score": 0.593,
    "raw_score": 0.593456,
    "tie_breaker": 0.603234,
    "decision_state": "CONFIDENT",  # NEW
    "confidence": 0.70,
    "confidence_factors": {  # NEW
        "score_contribution": 0.3500,
        "feature_quality": 0.2200,
        "feature_stability": 0.0900,
        "missing_penalty": 0.0400
    },
    "factors": [
        {
            "name": "rainfall",
            "weight": 0.15,
            "raw_value": 0.66,
            "contribution": 0.099
        },
        # ... more factors
    ]
}
```

### Enforcement Acknowledgment
```python
{
    "directive_id": "DIR-001-North",
    "action": "prioritize_irrigation",
    "target": "North",
    "status": "pending",
    "acknowledged": false,  
    "ack_timestamp": null,  
    "execution_status": "PENDING" 
}
```

---

## 🔧 Configuration & Customization

### Custom Event Store Path
```python
from event_sourcing import store_event
event = store_event(
    trace_id="MY-TRACE",
    event_type="INPUT",
    event_data=input_contract,
    event_store_path="custom_events.json"
)
```

### Custom Observability Log
```python
from observability import ObservabilityTracker
tracker = ObservabilityTracker(log_file="custom_telemetry.log")
tracker.record_stage_exit("TRACE-001", "sanskar", entry_time)
```

### Custom Schema Validation
```python
from schema_validation import SchemaValidator
validator = SchemaValidator()
# Validators auto-configured for all contracts
```

---

##  Error Handling

### Check for Failures
```python
result = run_tantra(input_contract)

if result["pipeline_status"] == "FAILED":
    failure = result["failure"]
    print(f"Error: {failure['code']} - {failure['message']}")
    print(f"Stage: {failure['stage']}")
```

### Validate Before Processing
```python
from schema_validation import get_validator
validator = get_validator()

validation = validator.validate_input(input_contract)
if validation["valid"]:
    result = run_tantra(input_contract)
else:
    print(f"Invalid contract: {validation['errors']}")
```

---

##  Performance Monitoring

### Check Stage Latencies
```python
obs = result["observability"]
total_latency = sum(obs["stage_latencies"].values())
print(f"Total pipeline latency: {total_latency:.2f} ms")
```

### Trace Specific Execution
```python
from observability import get_tracker
tracker = get_tracker()

trace_logs = tracker.get_trace_logs("TRACE-001")
for log in trace_logs:
    print(f"{log['stage']}: {log['latency_ms']}ms")
```

---

## Common Workflows

### Workflow 1: Check Uncertainty
```python
result = run_tantra(input_contract)
top_entity = result["sanskar_output"]["entities"][0]

if top_entity["decision_state"] == "AMBIGUOUS":
    print(" WARNING: Ambiguous ranking - manual review recommended")
elif top_entity["decision_state"] == "LOW_CONFIDENCE":
    print(" WARNING: Low confidence - reduced confidence applied")
else:
    print(" Confident ranking")
```

### Workflow 2: Audit Trail
```python
from observability import get_tracker
tracker = get_tracker()

trace_id = result["trace_id"]
logs = tracker.get_trace_logs(trace_id)

print(f"Execution history for {trace_id}:")
for log in logs:
    print(f"  {log['timestamp']}: {log['stage']} - {log['latency_ms']}ms")
```

### Workflow 3: Determinism Check
```python
# Execute
result1 = run_tantra(input_contract)

# Replay
result2 = run_tantra(input_contract, replay_mode=True)

# Compare
if result1["truth"]["pipeline_hash"] == result2["truth"]["pipeline_hash"]:
    print(" Determinism verified")
else:
    print(" Determinism broken!")
```

---

##  Troubleshooting

### Issue: ModuleNotFoundError
```python
# Ensure all new modules are in same directory
# Required: event_sourcing.py, observability.py, 
#           distributed_services.py, schema_validation.py
```

### Issue: Event Store Not Found
```python
# Event store created on first execution
# If custom path, ensure directory exists
from pathlib import Path
Path("custom_events_dir").mkdir(exist_ok=True)
```

### Issue: Low Confidence Warnings
```python
# Check decision_state field
# Confidence reduced when spread < 0.03
if entity["decision_state"] != "CONFIDENT":
    print(f"Spread likely < 0.03, confidence = {entity['confidence']}")
```

---

##  References

- **Uncertainty Detection**: `sanskar.py::detect_uncertainty_state()`
- **Confidence Engine**: `sanskar.py::build_entity_output()`
- **Event Sourcing**: `event_sourcing.py`
- **Observability**: `observability.py`
- **Services**: `distributed_services.py`
- **Validation**: `schema_validation.py`

---

##  Verification Checklist

After upgrade, verify:

-  All entities have `decision_state` field
-  All entities have `confidence_factors` object
-  Comparative explanation includes factor deltas
-  `event_store.json` grows with each execution
-  `observability.log` records all stages
-  Enforcement has `acknowledgment` object
-  Pipeline includes `observability` telemetry
-  Replay mode produces matching hashes

**If all , upgrade is successful!**
