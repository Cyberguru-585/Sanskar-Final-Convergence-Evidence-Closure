# SANSKAR Codebase Structure Exploration Report
**Date**: June 12, 2026 | **Status**: Current State Analysis Complete | **Thoroughness**: Medium

---

## Executive Summary

The SANSKAR system is a **bounded intelligence subsystem** designed to operate within the TANTRA ecosystem. The core ranking logic is **LIVE and deterministic**, with comprehensive trace/replay infrastructure. However, **external service integrations are mocked**, and **real process management/recovery is not yet implemented**. This report provides the foundation for Phase 1 (Runtime Legitimacy).

---

## 1. CORE RUNTIME COMPONENTS

### Main Entry Points

| Component | File | Function | Status |
|-----------|------|----------|--------|
| **Intelligence Engine** | `sanskar.py` | `run_sanskar(input_contract)` |  LIVE |
| **Decision Layer** | `core.py` | `run_core(sanskar_output)` |  LIVE |
| **Main Orchestrator** | `tantra.py` | `run_tantra(input_contract, replay_mode)` |  LIVE |
| **API Service** | `api.py` | FastAPI `/signal`, `/trace`, `/health` |  LIVE |

### Process Management Architecture

**Files**: `distributed_multiprocess_executor.py`, `distributed_services.py`

- **ProcessState machine**: INITIALIZING → HEALTHY → (DEGRADED | UNHEALTHY) → RECOVERING → (HEALTHY | DEAD)
- **ServiceMessage dataclass**: Typed inter-service communication with trace_id, content_hash, sequence_number
- **StageService base class**: Isolated execution pattern with `execute_isolated()` for failure containment
- **Service implementations**: SanskaarStageService, CoreStageService, EnforcementStageService
- **Redis fallback**: MockRedisClient (in-memory dict) when REDIS_AVAILABLE=False

**Current limitation**: Services are isolated logically but NOT spawned as real processes yet

---

## 2. SIMULATED vs. REAL BREAKDOWN

###  WHAT'S REAL (Actual Implementation)

**Scoring & Ranking** (sanskar.py):
- Feature scoring: rainfall (15%), temperature (12%), irrigation (18%), fertilizer (8%), yield_efficiency (28%), soil_quality (10%), weather (9%)
- Deterministic weighted calculation
- Confidence engine (4-factor model):
  - Score contribution: 50%
  - Feature quality: 25%
  - Feature stability: 15%
  - Missing data penalty: 10%
- Scenario analysis (rainfall +10%, temperature -2C)

**Trace Infrastructure** (event_sourcing.py, tantra.py):
- ✅ Event sourcing with immutable events
- ✅ Cryptographic hash chaining: `current_hash = SHA256(data + previous_hash)`
- ✅ Trace continuity verification across 5 stages
- ✅ Replay from stored events with hash validation
- ✅ Determinism proof: 5 identical runs → identical SHA-256

**Governance & Contracts** (runtime_adapters.py, governance_runtime_monitor.py):
- ✅ IntelligenceOutputContract, GovernanceDecisionContract validation
- ✅ Authority boundary validation (SANSKAR can do: ranking, signal generation; CANNOT do: governance, enforcement)
- ✅ ContractPhase enum (SIGNAL_SOURCE → SANSKAR → RAJYA → ENFORCEMENT → BUCKET → INSIGHT_BRIDGE)
- ✅ Fail-closed enforcer (fail_closed_enforcer.py)

**Observability** (observability.py, event_sourcing.py):
- ✅ Stage entry/exit recording with latency_ms
- ✅ Correlation ID tracking (trace_id → correlation_id → parent_trace_id)
- ✅ Decision state recording (CONFIDENT, AMBIGUOUS, LOW_CONFIDENCE)
- ✅ Error tracking with code/message
- ✅ JSON event log (observability.log)
- ✅ Console output formatting (console.py)

### ⚠️ WHAT'S SIMULATED (Mock Implementation)

**External Service Calls**:
- ⚠️ RAJYA governance: `RajyaMockGovernance` in test suite (10ms latency simulation)
- ⚠️ ENFORCEMENT: Local execution, no external call
- ⚠️ Bucket truth store: `BucketMockTruthStore` (simulated write)
- ⚠️ InsightBridge: Created in requests but never sent

**Process Execution**:
- ⚠️ `time.sleep()` delays for simulated async execution (async_orchestration.py)
- ⚠️ ProcessState tracking but NO actual subprocess spawning in core flow
- ⚠️ Mock Redis client (REDIS_AVAILABLE check falls back to in-memory dict)

**Failure Recovery**:
- ⚠️ Simulated retry logic with fixed backoff delays
- ⚠️ Circuit breaker state (no actual circuit opening)
- ⚠️ No real process restart verification
- ⚠️ No actual PID tracking/proof generation

**Deployment**:
- ⚠️ Docker-compose.yml references but containers not actually orchestrated
- ⚠️ Health endpoints basic (no real service status)

---

## 3. EXISTING RUNTIME INSTRUMENTATION

### Logging & Tracing (observability.py)

```python
class ObservabilityTracker:
    # Stage lifecycle
    record_stage_entry(trace_id, stage, contract_version, replay_mode)
    record_stage_exit(trace_id, stage, entry_time, decision_state, success, ...)
    
    # Decisions
    record_decision(trace_id, stage, decision_state, confidence, score, ...)
    
    # Errors
    record_error(trace_id, stage, code, message)
    
    # Correlation
    set_correlation_context(trace_id, parent_trace_id, correlation_id)
    get_correlation_context(trace_id)
```

**Output**: `observability.log` (newline-delimited JSON with timestamps, latency_ms, success flags)

### Console Display (console.py)

- `step(num, title)` — Stage number formatting
- `trace(trace_id)` — Trace ID display
- `entity_card(entity)` — Single entity formatting
- `ranking_board(entities)` — Comparison visualization
- `decision_display(output)` — Decision formatting
- `failure_display(failure)` — Failure formatting

### Event Sourcing (event_sourcing.py)

```python
store_event(trace_id, event_type, event_data)
# Produces: event_store.json with immutable events
# Fields: event_id, trace_id, event_type, data, event_hash, previous_event_hash, current_event_hash

replay_from_event(trace_id)
# Replays original input with hash verification

verify_lineage_integrity(trace_id)
# Detects mutations, deletions, corruption
```

### Health Checks & Authority Validation

- **api.py `/health`** — Basic endpoint (returns OK, needs enhancement)
- **governance_runtime_monitor.py** — Authority tracking
  - GovernanceViolationType: AUTHORITY_EXCEEDED, BOUNDARY_CROSSED, TRACE_MUTATED, etc.
  - GovernanceEvent: severity levels (CRITICAL, HIGH, MEDIUM)
  - AuthorityBoundaryValidator with authority_map

---

## 4. OBSERVABILITY & PROOF ARTIFACTS

### Existing Proof Files (Location: Root)

| Artifact | Purpose | Status |
|----------|---------|--------|
| `trace_continuity_proof.json` | Prove trace_id identical across all stages | ✅ Generated |
| `determinism_proof.json` | 5 identical runs with same SHA-256 | ✅ Generated |
| `failure_proof.json` | 3 broken input tests with trace preserved | ✅ Generated |
| `replay_divergence_proof.json` | Replay output matches original | ✅ Generated |
| `trace_reconstruction_proof.json` | Event lineage reconstruction | ✅ Generated |
| `runtime_boot_proof.json` | Real PIDs and timestamps | ⚠️ Referenced but needs regeneration |
| `runtime_hostile_suite.json` | 7 failure scenarios tested | ✅ Generated |
| `constitutional_convergence_proof.json` | Authority boundary enforcement | ✅ Generated |
| `api_contract_exchange_proof.json` | Contract validation at boundaries | ✅ Generated |
| `deployment_profiles_artifact.json` | Deployment configuration snapshots | ✅ Generated |

### Test/Demo Output Files

- `demo_output.txt` — Console output from demos
- `test_output.log` — Integration test logs
- `hardening_output.log` — Ecosystem hardening logs
- `integration_test_output.txt` — Integration results
- `full_chain_output.json` — Complete pipeline execution trace
- `stage_sanskar.json`, `stage_core.json`, `stage_enforcement.json`, `stage_truth.json` — Stage outputs
- `tantra_integration_test_report.json` — Test results (6/6 PASS)

### Event Store

- **event_store.json** — Immutable event log
  - Each event: event_id, trace_id, event_type (INPUT, etc.)
  - Cryptographic chaining: event_hash, previous_event_hash, current_event_hash
  - lineage_sequence, timestamp, immutable flag

---

## 5. INTEGRATION POINTS WITH EXTERNAL SYSTEMS

### Declared Chain

```
Signal → SANSKAR → RAJYA → ENFORCEMENT → Bucket → InsightBridge
```

### Current Integration Status

| System | Current State | Contract | Owner | Real | Mocked |
|--------|---------------|----------|-------|------|--------|
| **SANSKAR** | Input → ranking output | IntelligenceOutputContract | sanskar | ✅ | ❌ |
| **RAJYA** | Governance decision | GovernanceDecisionContract | rajya | ❌ | ✅ RajyaMockGovernance |
| **ENFORCEMENT** | Action directives | (local execution) | enforcement | ⚠️ | ✅ |
| **Bucket** | Truth storage | (simulated writes) | bucket | ❌ | ✅ BucketMockTruthStore |
| **InsightBridge** | Observability events | (created but not sent) | observability | ❌ | ✅ (ecosystem_integration.py) |

### Adapter Layer (adapter_layer/)

**Files**:
- `canonical_adapter.py` — Contract enforcement wrapper
- `contract_registry.json` — Contract version mapping
- `adapter_validation_proof.json` — Adapter testing results

**Key Classes**:
- `TraceContext` — Immutability validation
- `ContractPhase` enum — 6-stage pipeline
- `ContractOwnership` enum — Responsibility tracking
- `ContractHeader`, `ContractPayload` — Structured contracts
- `FailureMode` enum — 10 failure types (TIMEOUT, REJECTION, SCHEMA_MISMATCH, etc.)

**Status**: Schema defined, validation functions present, but not yet wired to external systems

### Integration Orchestration (ecosystem_integration.py)

- `create_rajya_request()` — Format SANSKAR → RAJYA handoff
- `simulate_rajya_response()` — Mock response
- `create_bucket_truth_request()` — Format truth store write
- `create_insightbridge_request()` — Format observability event

**Status**: All simulated, not sent to real systems

---

## 6. DEMO/TEST EXECUTION PATTERNS

### Demo Scripts

**demo_sanskar_upgrade.py** — 8 demonstrations:
1. Uncertainty detection — Shows decision_state per region
2. Confidence engine — 4-factor model breakdown
3. Comparative explanations — Advantages/disadvantages
4. Event replay — Determinism verification
5. Enforcement acknowledgment — Async execution
6. Observability — Trace logging
7. Distributed services — Isolated execution
8. Contract validation — Boundary enforcement

**demo_sanskar_upgrade_distributed.py** — 8 additional scenarios:
1. Append-only lineage
2. Distributed replay validation
3. Async execution simulation
4. External execution verification
5. Observability correlation
6. Schema evolution
7. Concurrency determinism
8. Governance uncertainty

### Test Suites

**tantra_integration_self_test.py** — 6-test suite:
1. `test_healthy_path()` — Normal execution
2. `test_invalid_input()` — Missing dataset/trace_id
3. `test_dependency_unavailable()` — RAJYA/Bucket down
4. `test_trace_break()` — Trace_id discontinuity
5. `test_authority_violation()` — Boundary crossing
6. `test_partial_failure()` — Upstream failure propagation

**Result**: `tantra_integration_test_report.json` (6/6 PASS)

**runtime_hostile_suite.py** — 7 failure scenarios:
1. SANSKAR crash + recovery with replay
2. RAJYA timeout + circuit breaker
3. Bucket unavailable + graceful degradation
4. Trace mutation detection
5. Authority violation blocking
6. Schema drift detection
7. Replay divergence detection

**Result**: `runtime_hostile_suite.json` (7/7 scenarios tested)

**constitutional_pressure_tests.py** — Authority boundary tests

**ecosystem_instability_suite.py** — Cross-ecosystem failure tests

### How Proofs are Generated

```python
# 1. Execute test scenario
result = run_tantra(input_contract)

# 2. Record traces/events
store_event(trace_id, "INPUT", input_contract)
tracker.record_stage_exit(trace_id, "sanskar", entry_time, ...)

# 3. Verify continuity
proof = verify_trace_continuity(trace_id, stages)

# 4. Compute integrity hash
chain_hash = compute_chain_hash(data)

# 5. Save to JSON artifact
with open(f"{proof_name}.json", "w") as f:
    json.dump(proof_data, f, indent=2)
```

### Self-Test Execution

```bash
# Run integration tests (6 test cases)
python tantra_integration_self_test.py
# Output: tantra_integration_test_report.json

# Run hostile scenarios (7 scenarios)
python runtime_hostile_suite.py
# Output: runtime_hostile_suite.json

# Run demo with 8 scenarios
python demo_sanskar_upgrade.py
# Output: demo_output.txt, stage_*.json files

# Run API service
python api.py
# Endpoints: /signal, /trace/{trace_id}, /health, /replay
```

---

## CURRENT STATE READINESS

###  READY FOR PHASE 1
- Core ranking logic (fast, deterministic)
- Trace continuity verification
- Replay determinism
- Contract schema validation
- Test suite infrastructure
- Observability instrumentation

###  NEEDS REAL IMPLEMENTATION (PHASE 1 CRITICAL)
- Real process spawning and PID tracking
- Real service health checks
- Real ecosystem chain execution (not mocked)
- Real failure injection and recovery
- Real authority boundary enforcement
- Runtime boot/restart proof generation

###  TODO (PHASE 1 MANDATORY)
- `runtime_legitimacy_report.md` — Narrative proof
- `runtime_boot_proof.json` — Real PIDs, args, timestamps
- `runtime_restart_proof.json` — Restart sequence + state preservation
- `service_health_proof.json` — Health endpoint validation
- Real RAJYA/Bucket/InsightBridge integration
- Failure recovery demonstrations

---

## KEY FILES REFERENCE

### By Category

**Core Logic** (209 lines total):
- [sanskar.py](sanskar.py) — Intelligence ranking (399 lines)
- [core.py](core.py) — Decision layer (105 lines)
- [enforcement.py](enforcement.py) — Action directives
- [tantra.py](tantra.py) — Main orchestrator

**Contracts & Boundaries** (200+ lines):
- [runtime_adapters.py](runtime_adapters.py) — Contract enforcement
- [adapter_layer/canonical_adapter.py](adapter_layer/canonical_adapter.py) — Contract headers
- [governance_runtime_monitor.py](governance_runtime_monitor.py) — Authority validation

**Instrumentation** (200+ lines):
- [observability.py](observability.py) — Tracing system
- [event_sourcing.py](event_sourcing.py) — Event stream
- [console.py](console.py) — Output formatting

**Integration & Distribution** (300+ lines):
- [ecosystem_integration.py](ecosystem_integration.py) — External handoffs
- [distributed_services.py](distributed_services.py) — Isolated services
- [distributed_multiprocess_executor.py](distributed_multiprocess_executor.py) — Process management
- [async_orchestration.py](async_orchestration.py) — Async queuing

**Testing** (1000+ lines):
- [tantra_integration_self_test.py](tantra_integration_self_test.py) — 6-test suite
- [runtime_hostile_suite.py](runtime_hostile_suite.py) — 7 failure scenarios
- [demo_sanskar_upgrade.py](demo_sanskar_upgrade.py) — 8 demos
- [demo_sanskar_upgrade_distributed.py](demo_sanskar_upgrade_distributed.py) — 8 more demos

**Configuration**:
- [runtime_config/](runtime_config/) — Config files
- [deployment_profiles_artifact.json](deployment_profiles_artifact.json) — Deployment snapshots
- [service_registry.json](service_registry.json) — Service endpoints

---

## PHASE 1 IMPLEMENTATION ROADMAP

### Priority 1: Real Runtime Execution
1. **Modify [distributed_multiprocess_executor.py](distributed_multiprocess_executor.py)**
   - Spawn real processes (currently mocked)
   - Capture PIDs, process args, timestamps
   - Implement signal handling (SIGTERM, SIGKILL)

2. **Generate runtime_boot_proof.json**
   - PID, parent PID, command line args
   - Timestamp (UTC ISO format)
   - Process state transitions

3. **Generate runtime_restart_proof.json**
   - Original process death
   - Restart sequence (kill, detect, restart)
   - State recovery from event store

### Priority 2: External Service Integration
1. **Wire RAJYA**: Replace RajyaMockGovernance with real RAJYA service calls
2. **Wire Bucket**: Replace BucketMockTruthStore with real S3-like backend
3. **Wire InsightBridge**: Send observability events to real system
4. **Generate ecosystem_convergence_proof.json**: Trace visible across all 6 stages

### Priority 3: Failure Scenarios
1. **Execute runtime_hostile_suite.py against real processes**
2. **Capture failure moments (logs, state, error signals)**
3. **Verify recovery procedures**
4. **Generate runtime_failure_matrix.json**

### Priority 4: Health Checks
1. **Enhance [api.py](api.py) /health endpoint**
2. **Real service status checks**
3. **Generate service_health_proof.json**

---

## CONCLUSION

SANSKAR's core deterministic logic is **SOLID and TESTED**. The infrastructure for proof generation, trace continuity, and replay is **COMPLETE**. The primary gap is **real external service integration and process management**—which is exactly what Phase 1 is designed to address.

**Entry point for Phase 1**: Start with [distributed_multiprocess_executor.py](distributed_multiprocess_executor.py) to enable real process spawning and PID tracking, then generate runtime proofs.

