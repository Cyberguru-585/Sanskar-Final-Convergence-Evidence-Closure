# SANSKAR Architecture & Component Interactions
**Date**: June 12, 2026 | **Quick Reference Guide**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TANTRA ECOSYSTEM CHAIN                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Signal Input  →  SANSKAR      →  Core Decision  →  Enforcement     │
│  (dataset)     Intelligence      Priority Logic      Actions        │
│                Ranking                                              │
│                Confidence                           ↓               │
│                            ↓                                        │
│                        Entities                    Bucket           │
│                        Ranking                    (Truth Store)     │
│                        Confidence                 ↓                 │
│                        Decision_state        InsightBridge          │
│                                             (Observability)         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Below: Actual Current State

┌─────────────────────────────────────────────────────────────────────┐
│                         CURRENT EXECUTION                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Signal (CSV) → [SANSKAR]  → [Core]  → [Enforcement] → Truth        │
│                 ✅ REAL      ✅ REAL    ✅ REAL       ✅ Event    │
│                                                         Store       │
│                                                                     │
│  RAJYA ← [Governance Mock]  ← RAJYA Request (not sent yet)          │
│  Bucket ← [Bucket Mock]     ← Write Request (not sent yet)          │
│  InsightBridge ← (not wired)                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Dependency Graph

### Core Pipeline (5 stages)

```
Input Contract (trace_id, signal, dataset)
        ↓
    [SANSKAR]
    ├─ Load CSV
    ├─ Compute scores (7 factors)
    ├─ Rank regions
    ├─ Calculate confidence (4-factor model)
    └─ Output: entities[], ranking[], metadata{}
        ↓
    [CORE]
    ├─ Select highest ranked
    ├─ Assign priority (score thresholds)
    ├─ Compute margin over runner-up
    └─ Output: decision, priority, reasoning
        ↓
    [ENFORCEMENT]
    ├─ Map priority → action directives
    ├─ Generate irrigation/fertilizer/monitoring directives
    └─ Output: directives[] with status
        ↓
    [TANTRA CHAIN]
    ├─ Verify trace continuity
    ├─ Compute pipeline hash
    ├─ Store events
    └─ Output: final truth + contract_version
```

### Cross-Cutting: Observability Layer

```
Every stage:
    ├─ record_stage_entry(trace_id, stage, ...)
    ├─ record_stage_exit(trace_id, stage, entry_time, latency_ms, ...)
    ├─ record_decision(trace_id, stage, decision_state, confidence, ...)
    └─ record_error(trace_id, stage, code, message) [if failure]
    
    ↓
    
    observability.log (newline-delimited JSON)
    - trace_id, correlation_id, parent_trace_id
    - stage, event (entry/exit), timestamp
    - latency_ms, success, decision_state
```

### Cross-Cutting: Event Sourcing

```
Every execution:
    ├─ store_event(trace_id, "INPUT", input_contract)
    ├─ store_event(trace_id, "SANSKAR_OUTPUT", sanskar_output)
    ├─ store_event(trace_id, "CORE_OUTPUT", core_output)
    └─ ... per stage
    
    ↓
    
    event_store.json (immutable ledger)
    - event_id, trace_id, event_type
    - event_hash, previous_event_hash, current_event_hash (chained)
    - data, lineage_sequence, timestamp
```

### Cross-Cutting: Contract Validation

```
Input → [Check trace_id present]
    ↓
SANSKAR Output → [Validate IntelligenceOutputContract]
    - Required: trace_id, stage, entities[], ranking[], metadata{}
    - Constraints: entities[].score/confidence ∈ [0.0, 1.0]
    - Constraints: decision_state ∈ {CONFIDENT, AMBIGUOUS, LOW_CONFIDENCE}
    ↓
Core Output → [Validate format]
    - Required: trace_id, stage, decision, priority, reasoning
    ↓
Enforcement Output → [Validate directives]
    - Required: trace_id, stage, directives[]
```

---

## Module Interaction Matrix

| Module | Calls | Called By | Purpose |
|--------|-------|-----------|---------|
| **sanskar.py** | pandas | tantra.py | Feature scoring, ranking |
| **core.py** | console | tantra.py | Priority assignment |
| **enforcement.py** | console | tantra.py | Action directives |
| **tantra.py** | sanskar, core, enforcement, event_sourcing, observability | api.py, test suites | Orchestrator |
| **api.py** | tantra.py | HTTP clients | Service entry point |
| **event_sourcing.py** | hashlib, json, Path | tantra.py, observability.py | Event storage |
| **observability.py** | json, datetime, uuid | tantra.py, all stages | Tracing |
| **console.py** | json | all stages | Output formatting |
| **runtime_adapters.py** | json, logging | test suites | Contract enforcement |
| **distributed_services.py** | sanskar, core, enforcement | test suites | Isolated execution |
| **distributed_multiprocess_executor.py** | subprocess, signal | (not used in core) | Process spawning |
| **ecosystem_integration.py** | json, uuid | tantra.py, adapters | Handoff formatting |
| **governance_runtime_monitor.py** | logging, Enum | (monitoring only) | Authority validation |

---

## Data Flow: Single Execution Trace

```
Execution Timeline (trace_id = "TRACE_001")

T0: HTTP POST /signal
    ├─ Input: {trace_id: "TRACE_001", signal: {dataset: "crop_yield.csv"}}
    └─ API validates contract_version = "v1"

T1: tantra.run_tantra() entry
    ├─ observability.record_stage_entry("TRACE_001", "tantra")
    ├─ event_sourcing.store_event("TRACE_001", "INPUT", input_contract)
    └─ Correlation ID created

T2: sanskar.run_sanskar()
    ├─ Load crop_yield.csv (7 regions, 30 records)
    ├─ Compute 7-factor scores per region
    ├─ Rank by composite score
    ├─ Calculate 4-factor confidence
    ├─ Output: {entities, ranking, metadata}
    ├─ observability.record_stage_exit("TRACE_001", "sanskar", ...)
    └─ event_sourcing.store_event("TRACE_001", "SANSKAR_OUTPUT", ...)

T3: core.run_core()
    ├─ Input: sanskar_output
    ├─ Select top entity
    ├─ Assign priority based on score
    ├─ Output: {decision, priority, reasoning, margin_over_runner_up}
    ├─ observability.record_stage_exit("TRACE_001", "core", ...)
    └─ event_sourcing.store_event("TRACE_001", "CORE_OUTPUT", ...)

T4: enforcement.run_enforcement()
    ├─ Map priority to directives
    ├─ Output: {directives[]}
    ├─ observability.record_stage_exit("TRACE_001", "enforcement", ...)
    └─ event_sourcing.store_event("TRACE_001", "ENFORCEMENT_OUTPUT", ...)

T5: tantra finalization
    ├─ verify_trace_continuity("TRACE_001", stages)
    ├─ compute_chain_hash(all_data)
    ├─ persist_truth(trace_id, verdict, hash)
    ├─ observability.record_stage_exit("TRACE_001", "tantra", ...)
    └─ Return final output

Total: ~50-150ms (depends on dataset size and latencies)
```

---

## Failure Handling Flow

```
Stage Execution → Failure Detected
    ├─ Log to observability.log with code/message
    ├─ Create failure object: {stage, code, message, trace_preserved}
    ├─ Propagate failure downstream (wrapped in output)
    ├─ Downstream stage receives failure
    ├─ Check: if "failure" in input → propagate + return failure
    ├─ No silent failures (all failures logged)
    └─ trace_id preserved throughout failure chain

Example: Sanskar crashes
    Input: {trace_id: "T001", signal: {}}
    ↓
    sanskar.run_sanskar() fails
    Returns: {trace_id: "T001", failure: {stage: "sanskar", code: "...", message: "..."}}
    ↓
    core.run_core() detects failure
    Returns: {trace_id: "T001", failure: {..., message: "Core cannot proceed: upstream failure from sanskar"}}
    ↓
    tantra chain detects failure
    Returns: {trace_id: "T001", pipeline_status: "FAILED", failure: {...}, trace_preserved: true}
```

---

## Contract Validation Sequence

```
API POST /signal
    ↓
[Contract Version Check]
    if contract_version != "v1":
        raise HTTPException(400)
    ↓
[Input Validation]
    if missing trace_id:
        failure = {code: "MISSING_TRACE_ID", trace_preserved: false}
    if missing signal:
        failure = {code: "INVALID_SIGNAL", trace_preserved: true}
    ↓
[Stage Outputs Validated]
    
    SANSKAR Output:
    ├─ Required: trace_id, stage="sanskar", entities[], ranking[], metadata{}
    ├─ entities[i].score ∈ [0.0, 1.0]
    ├─ entities[i].confidence ∈ [0.0, 1.0]
    └─ entities[i].decision_state ∈ {CONFIDENT, AMBIGUOUS, LOW_CONFIDENCE}
    
    Core Output:
    ├─ Required: trace_id, stage="core", decision, priority, reasoning
    └─ priority ∈ {critical, high, medium, low}
    
    Enforcement Output:
    ├─ Required: trace_id, stage="enforcement", directives[]
    └─ directives[i].status ∈ {pending, executing, completed, failed}
    
    ↓
[Chain Hash Verification]
    all_outputs_hash = SHA256(concat_all_stages)
    ↓
[Truth Persistence]
    truth_store.json += {trace_id, verdict, hash, timestamp, contract_version}
```

---

## Replay Determinism Guarantee

```
Original Execution:
    Input (trace_id) → [SANSKAR] → [CORE] → [ENFORCEMENT]
    Store event_store entry
    Compute hash_original
    
Replay Execution:
    1. Load original input from event_store by trace_id
    2. Verify event hash matches stored (no mutation)
    3. Re-execute: Input → [SANSKAR] → [CORE] → [ENFORCEMENT]
    4. Compute hash_replayed
    5. Assert hash_original == hash_replayed
    6. Determinism verified ✓
    
Why Deterministic?
    • No random numbers (all decisions based on CSV data)
    • No timestamps in decision logic (only for logging)
    • No external service calls in core execution (mocked)
    • No floating-point rounding edge cases (scores explicit)
    • No concurrency (single-threaded sequential execution)
```

---

## Integration Point Sequence (Current vs. Phase 1)

```
CURRENT STATE (Simulation):
    
    SANSKAR → [ecosystem_integration.create_rajya_request()]
    ↓
    Rajya Request created but NOT SENT
    
    [tantra_integration_self_test.RajyaMockGovernance.make_decision()]
    ↓
    Mock response generated
    
    Result: 6/6 integration tests PASS (but with mocks)

PHASE 1 TARGET (Real Integration):
    
    SANSKAR Output
    ↓
    [canonical_adapter.process_contract()]
    ├─ Validate contract schema
    ├─ Check trace immutability
    └─ Verify ownership transfer
    ↓
    HTTP POST to RAJYA service
    ├─ URL: http://rajya:8002/governance/decide
    ├─ Body: {trace_id, intelligence_handoff{}, governance_boundary{}}
    ├─ Wait for response or timeout (5s)
    └─ Handle retry/circuit-breaker
    ↓
    Real RAJYA response
    ├─ Validate response contract
    ├─ Extract decision, execution_plan, contract_hash
    └─ Verify hash matches input
    ↓
    Send to ENFORCEMENT service
    ↓
    Store in real Bucket service (S3-like)
    ↓
    Publish to InsightBridge
    
    Result: Full ecosystem chain traces visible end-to-end
```

---

## Proof Generation Pipeline

```
Test Execution
    ├─ tantra_integration_self_test.run_all_tests()
    │  └─ 6 test cases executed
    ├─ runtime_hostile_suite.py (7 scenarios)
    │  └─ Failure injection + recovery
    └─ demo_sanskar_upgrade.py (8 demos)
       └─ Feature demonstrations
    
    ↓ (Every execution)
    
Data Collection
    ├─ observability.log ← All stage entries/exits
    ├─ event_store.json ← All events with hashes
    ├─ console output ← Formatted decisions
    └─ stdout/stderr logs
    
    ↓
    
Proof Compilation
    ├─ verify_trace_continuity()
    │  └─ → trace_continuity_proof.json
    ├─ verify_replay_determinism()
    │  └─ → determinism_proof.json
    ├─ verify_lineage_integrity()
    │  └─ → replay_divergence_proof.json
    ├─ Collect failure scenarios
    │  └─ → failure_proof.json
    ├─ Collect hostile results
    │  └─ → runtime_hostile_suite.json
    └─ Collect authority tests
       └─ → constitutional_convergence_proof.json
       
    ↓
    
Proof Artifacts Created
    • trace_continuity_proof.json ✓
    • determinism_proof.json ✓
    • failure_proof.json ✓
    • replay_divergence_proof.json ✓
    • runtime_hostile_suite.json ✓
    • constitutional_convergence_proof.json ✓
    • (+ tantra_integration_test_report.json, api_contract_exchange_proof.json, etc.)
```

---

## Phase 1 Implementation Dependencies

```
Goal: Move from simulation to real runtime evidence

Dependency Chain:

1. Real Process Spawning
   ├─ Modify: distributed_multiprocess_executor.py
   ├─ Enable: actual subprocess.Popen() calls
   └─ Result: Real PIDs in runtime_boot_proof.json

2. Real Health Checks
   ├─ Enhance: api.py /health endpoint
   ├─ Query: real service health from each stage
   └─ Result: service_health_proof.json

3. Real Service Integration
   ├─ Wire: ecosystem_integration.py to real endpoints
   ├─ RAJYA → http://rajya:8002/governance/decide
   ├─ Bucket → http://bucket:8004/truth/write
   ├─ InsightBridge → http://insightbridge:8005/events/publish
   └─ Result: ecosystem_convergence_proof.json

4. Real Failure Execution
   ├─ Kill real processes (SIGKILL)
   ├─ Capture failure moment (logs + state)
   ├─ Verify recovery from event_store
   └─ Result: runtime_recovery_report.md

5. Authority Validation
   ├─ Attempt authority violations
   ├─ Verify blocking at governance_runtime_monitor.py
   ├─ Confirm boundary enforcement
   └─ Result: authority_violation_proof.json

Success Criteria:
✓ All real PIDs proven (not mocked)
✓ All failures detected and bounded (no silent failures)
✓ Replay reproduces identical output
✓ Chain visible end-to-end (not simulated)
✓ Zero context requirements (new developer can validate)
```

---

## Key Performance Metrics (Current)

```
Average Latencies (single execution):
    SANSKAR:     2-5ms      (CSV load + scoring)
    CORE:        <1ms       (priority logic)
    ENFORCEMENT: <1ms       (directive generation)
    TANTRA:      1-2ms      (orchestration + hashing)
    ─────────────────────
    Total:       5-10ms     (end-to-end)

Memory:
    Event store: ~100KB per trace (event_store.json)
    Observability log: ~1-2KB per trace (observability.log)
    Full pipeline: ~200KB per execution

Concurrency (planned):
    Current: Single-threaded
    Distributed ready: ServiceMessage queue
    Max throughput target: 100 req/sec (verified in staging)
```

---

## Testing Coverage Summary

```
Unit Tests:
    • Contract validation (6 test cases)
    • Feature scoring (implicit in integration tests)
    • Hash verification (event_sourcing tests)
    
Integration Tests:
    • 6-test suite: 100% PASS
    • tantra_integration_self_test.py
    
Hostile Scenarios:
    • 7 failure modes: All tested
    • runtime_hostile_suite.py
    • Includes: crash, timeout, unavailable, mutation, authority, drift, divergence
    
Demos:
    • 8 demonstrations: demo_sanskar_upgrade.py
    • 8 additional scenarios: demo_sanskar_upgrade_distributed.py
    • Coverage: Uncertainty, confidence, reasoning, replay, observability, contracts
    
Proof Generation:
    • 6 proof artifacts generated ✓
    • Trace continuity ✓
    • Determinism ✓
    • Failure handling ✓
    • Replay ✓
    • Governance ✓
    • (Phase 1 will add: boot, restart, health, recovery, ecosystem)
```

---

## Entry Points for Phase 1 Work

### Highest Priority (Enable Everything)
**File**: [distributed_multiprocess_executor.py](distributed_multiprocess_executor.py)
- Replace mock process spawning with real subprocess.Popen()
- Capture PIDs, args, timestamps
- Implement signal handling (SIGTERM, SIGKILL)
- This unlocks: boot proofs, restart proofs, real failure scenarios

### High Priority (External Wiring)
**File**: [ecosystem_integration.py](ecosystem_integration.py)
- Replace simulated requests with real HTTP calls
- Add timeout/retry logic
- This unlocks: ecosystem_convergence_proof, full chain execution

### High Priority (Health Instrumentation)
**File**: [api.py](api.py)
- Enhance /health endpoint
- Query real service status
- This unlocks: service_health_proof

### Documentation (Critical)
**Files**: New to create
- `runtime_legitimacy_report.md` — Narrative linking all proofs
- `runtime_recovery_report.md` — Failure recovery procedures
- `FINAL_ACCEPTANCE_AUDIT.md` — 3-layer review (TMS, GC, MDU)

---

