# SANSKAR Codebase File Inventory & Quick Navigation
**Date**: June 12, 2026 | **Updated**: Complete Exploration

---

## CORE EXECUTION PIPELINE (5 Files, ~650 lines)

| File | Lines | Purpose | Status | Entry Point |
|------|-------|---------|--------|-------------|
| **sanskar.py** | 399 | Intelligence ranking engine | ✅ LIVE | `run_sanskar(input_contract)` |
| **core.py** | 105 | Decision layer (priority assignment) | ✅ LIVE | `run_core(sanskar_output)` |
| **enforcement.py** | ~100 | Action directives | ✅ LIVE | `run_enforcement(core_output)` |
| **tantra.py** | ~300 | Main orchestrator | ✅ LIVE | `run_tantra(input_contract, replay_mode=False)` |
| **api.py** | ~150 | FastAPI service wrapper | ✅ LIVE | `POST /signal, GET /trace/{trace_id}` |

---

## INSTRUMENTATION & OBSERVABILITY (4 Files, ~800 lines)

| File | Lines | Purpose | Status | Key Classes |
|------|-------|---------|--------|-------------|
| **observability.py** | ~200 | Tracing system | ✅ LIVE | `ObservabilityTracker` |
| **event_sourcing.py** | ~200 | Event stream with hash chaining | ✅ LIVE | `store_event()`, `replay_from_event()` |
| **console.py** | ~300 | Output formatting | ✅ LIVE | `step()`, `entity_card()`, `decision_display()` |
| **causality_tracker.py** | ~100 | Causality tracking | ✅ LIVE | `CausalityTracker` |

---

## CONTRACT & GOVERNANCE (3 Files, ~400 lines)

| File | Lines | Purpose | Status | Key Classes |
|------|-------|---------|--------|-------------|
| **runtime_adapters.py** | ~250 | Contract enforcement | ✅ LIVE | `IntelligenceOutputContract`, `GovernanceDecisionContract` |
| **governance_runtime_monitor.py** | ~150 | Authority validation | ✅ LIVE | `AuthorityBoundaryValidator`, `GovernanceEvent` |
| **fail_closed_enforcer.py** | ~100 | Fail-closed execution | ✅ LIVE | `FailClosedEnforcer` |

---

## DISTRIBUTION & INTEGRATION (4 Files, ~500 lines)

| File | Lines | Purpose | Status | Key Classes |
|------|-------|---------|--------|-------------|
| **distributed_services.py** | ~150 | Isolated service pattern | ✅ LIVE | `StageService`, `SanskaarStageService`, etc. |
| **distributed_multiprocess_executor.py** | ~300 | Process management | ⚠️ MOCK | `ServiceMessage`, `ProcessState` |
| **ecosystem_integration.py** | ~200 | External handoffs (RAJYA/Bucket/InsightBridge) | ⚠️ MOCK | `EcosystemIntegration` |
| **async_orchestration.py** | ~150 | Async execution queuing | ⚠️ MOCK | `AsyncOrchestrator`, `ExecutionState` |

---

## ADAPTER LAYER (3 Files, ~350 lines)

| File | Lines | Purpose | Status | Key Classes |
|------|-------|---------|--------|-------------|
| **adapter_layer/canonical_adapter.py** | ~300 | Contract enforcement wrapper | ✅ DEFINED | `TraceContext`, `ContractPhase`, `ContractPayload` |
| **adapter_layer/contract_registry.json** | ~50 | Contract version mapping | ✅ CONFIG | JSON registry |
| **adapter_layer/adapter_validation_proof.json** | ~100 | Adapter testing results | ✅ ARTIFACT | Proof data |

---

## INTELLIGENT FEATURES (3 Files, ~500 lines)

| File | Lines | Purpose | Status | Key Features |
|------|-------|---------|--------|-------------|
| **adaptive_intelligence.py** | ~200 | Adaptive refinement & confidence engine | ✅ LIVE | 4-factor confidence model, decision_state |
| **schema_validation.py** | ~150 | Schema evolution & versioning | ✅ LIVE | Version checking, compatibility |
| **schema_evolution.py** | ~150 | Contract schema management | ✅ LIVE | Schema versioning, evolution tracking |

---

## TEST SUITES (6 Files, ~1200 lines)

| File | Lines | Purpose | Status | Coverage |
|------|-------|---------|--------|----------|
| **tantra_integration_self_test.py** | ~400 | Main integration test suite | ✅ LIVE | 6 test cases: healthy, invalid, unavailable, trace_break, authority, partial_failure |
| **runtime_hostile_suite.py** | ~300 | Failure scenario tests | ✅ LIVE | 7 scenarios: crash, timeout, unavailable, mutation, authority, drift, divergence |
| **constitutional_pressure_tests.py** | ~250 | Authority boundary pressure tests | ✅ LIVE | Authority matrix, boundary enforcement |
| **ecosystem_instability_suite.py** | ~200 | Cross-ecosystem failure tests | ✅ LIVE | Integration failure scenarios |
| **concurrency_test_engine.py** | ~150 | Concurrency testing | ✅ LIVE | Parallel execution, stress tests |
| **verification_harness.py** | ~100 | General verification | ✅ LIVE | Verification utilities |

---

## DEMO SCRIPTS (4 Files, ~800 lines)

| File | Lines | Purpose | Status | Demos |
|------|-------|---------|--------|-------|
| **demo_sanskar_upgrade.py** | ~400 | 8 core demonstrations | ✅ LIVE | Uncertainty, confidence, reasoning, replay, ack, observability, services, contracts |
| **demo_sanskar_upgrade_distributed.py** | ~300 | 8 distributed scenarios | ✅ LIVE | Lineage, replay validation, async, verification, correlation, schema, concurrency, governance |
| **operational_readiness_demo.py** | ~50 | Operational readiness checks | ✅ LIVE | Deployment validation |
| **demo_convergence_completion.py** | ~50 | Convergence validation | ✅ LIVE | Convergence checks |

---

## CONFIGURATION & PROFILES (3 Files)

| File | Lines | Purpose | Status | Content |
|------|-------|---------|--------|---------|
| **runtime_config/** | — | Runtime configuration files | ✅ CONFIG | SANSKAR, RAJYA, ENFORCEMENT, TRUTH configs |
| **deployment_profiles_artifact.json** | ~100 | Deployment snapshots | ✅ ARTIFACT | Staging, production profiles |
| **service_registry.json** | ~50 | Service endpoint registry | ✅ CONFIG | Service URLs and metadata |

---

## PROOF & VERIFICATION ARTIFACTS (12+ Files)

### Generated Proofs (Location: Root)

| Artifact | Lines | Status | Proof Type | Usage |
|----------|-------|--------|-----------|-------|
| **trace_continuity_proof.json** | ~50 | ✅ | Trace integrity | Prove trace_id identical across stages |
| **determinism_proof.json** | ~100 | ✅ | Execution consistency | 5 identical runs, same SHA-256 |
| **failure_proof.json** | ~80 | ✅ | Failure handling | 3 broken input tests with trace preservation |
| **replay_divergence_proof.json** | ~150 | ✅ | Replay fidelity | Replay output matches original |
| **trace_reconstruction_proof.json** | ~100 | ✅ | Event lineage | Lineage reconstruction from events |
| **runtime_boot_proof.json** | ~80 | ⚠️ REFERENCED | Runtime legitimacy | Real PIDs, args, timestamps (NEEDS REGEN) |
| **runtime_hostile_suite.json** | ~300 | ✅ | Failure scenarios | 7 hostile scenarios tested |
| **constitutional_convergence_proof.json** | ~200 | ✅ | Authority enforcement | Authority boundary tests |
| **api_contract_exchange_proof.json** | ~200 | ✅ | Contract validation | Contract enforcement at boundaries |
| **deployment_profiles_artifact.json** | ~100 | ✅ | Deployment proof | Configuration snapshots |
| **tantra_integration_test_report.json** | ~50 | ✅ | Test results | 6/6 tests PASS |
| **federated_verification_proof.json** | ~100 | ✅ | Distributed verification | Federated verification results |

---

## DOCUMENTATION (8 Files)

| File | Purpose | Status | Audience |
|------|---------|--------|----------|
| **README.md** | System overview | ✅ LIVE | All |
| **AUTHORITY_MATRIX.md** | Authority boundaries | ✅ COMPLETE | Architects, Reviewers |
| **TANTRA_PLACEMENT.md** | Ecosystem role | ✅ COMPLETE | Architects |
| **DEPLOYMENT_NOTES.md** | Deployment procedures | ✅ COMPLETE | Operators |
| **OPERATOR_MANUAL.md** | Operator procedures | ✅ COMPLETE | Operators |
| **FAQ.md** | Common questions | ✅ LIVE | All |
| **DRIFT_CHECKS.md** | Governance drift detection | ✅ COMPLETE | Architects |
| **TRACE_SCHEMA_PROVENANCE.md** | Trace/schema lineage | ✅ COMPLETE | Architects |

---

## EXPLORATION DOCUMENTS (3 New Files)

| File | Purpose | Status | Audience |
|------|---------|--------|----------|
| **CODEBASE_EXPLORATION_REPORT.md** | ← This exploration | ✅ NEW | All |
| **ARCHITECTURE_REFERENCE.md** | Visual diagrams and flows | ✅ NEW | Architects, Engineers |
| **FILE_INVENTORY.md** | ← This file | ✅ NEW | All |

---

## DATA FILES (5 Files)

| File | Content | Size | Status |
|------|---------|------|--------|
| **crop_yield.csv** | Test dataset (30 regions × 7 factors) | ~10KB | ✅ |
| **event_store.json** | Immutable event log | ~100KB/trace | ✅ |
| **truth_store.json** | Truth entries | ~50KB | ✅ |
| **observability.log** | Tracing log (newline-delimited JSON) | ~2KB/trace | ✅ |
| **console_output.txt** | Console display output | ~50KB | ✅ |

---

## STARTUP/DEPLOYMENT (4 Files)

| File | Purpose | Status | OS |
|------|---------|--------|-----|
| **startup.sh** | Start services | ✅ LIVE | Linux/Mac |
| **startup.bat** | Start services | ✅ LIVE | Windows |
| **shutdown.sh** | Stop services | ✅ LIVE | Linux/Mac |
| **docker-compose.yml** | Container orchestration | ⚠️ REFERENCED | All |
| **Dockerfile** | Container image | ⚠️ REFERENCED | All |

---

## PHASE 1 CRITICAL FILES (Prioritize These)

### Must Modify (Real Implementation):
1. **distributed_multiprocess_executor.py** — Real process spawning
2. **ecosystem_integration.py** — Real external service calls
3. **api.py** — Real health checks

### Must Create (Phase 1 Deliverables):
1. **runtime_legitimacy_report.md** — Narrative proof
2. **runtime_boot_proof.json** — Real PIDs
3. **runtime_restart_proof.json** — Restart sequence
4. **service_health_proof.json** — Health validation
5. **ecosystem_convergence_proof.json** — Full chain execution
6. **runtime_recovery_report.md** — Failure recovery
7. **authority_violation_proof.json** — Boundary enforcement
8. **runtime_failure_matrix.json** — Failure scenarios
9. **FINAL_ACCEPTANCE_AUDIT.md** — 3-layer review

---

## QUICK REFERENCE: FILE LOCATIONS BY FEATURE

### "I want to understand ranking logic"
→ [sanskar.py](sanskar.py) lines 1-100

### "I want to understand decision logic"
→ [core.py](core.py) lines 1-50

### "I want to understand trace continuity"
→ [event_sourcing.py](event_sourcing.py) + [tantra.py](tantra.py) verify_trace_continuity()

### "I want to understand contract enforcement"
→ [runtime_adapters.py](runtime_adapters.py) + [adapter_layer/canonical_adapter.py](adapter_layer/canonical_adapter.py)

### "I want to run tests"
→ `python tantra_integration_self_test.py` (6 tests)
→ `python runtime_hostile_suite.py` (7 scenarios)

### "I want to run a demo"
→ `python demo_sanskar_upgrade.py` (8 demos)

### "I want to understand architecture"
→ [ARCHITECTURE_REFERENCE.md](ARCHITECTURE_REFERENCE.md) (this document)

### "I want to check current status"
→ [DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md)

### "I want to understand boundaries"
→ [AUTHORITY_MATRIX.md](AUTHORITY_MATRIX.md)

### "I want to deploy"
→ [DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md) Scenario sections

### "I want to operate"
→ [OPERATOR_MANUAL.md](OPERATOR_MANUAL.md)

---

## CODE STATISTICS

```
Total Python Lines: ~5,000+
├─ Core Pipeline: 650 lines
├─ Instrumentation: 800 lines
├─ Contracts: 400 lines
├─ Distribution: 500 lines
├─ Adapters: 350 lines
├─ Features: 500 lines
└─ Tests/Demos: 2,000+ lines

Documentation: ~3,000+ lines
├─ Exploration: ~1,500 lines (this exercise)
├─ Deployment: ~800 lines
├─ Architecture: ~800 lines
└─ Operator: ~1,000+ lines

JSON Artifacts: ~2,000+ lines
├─ Proof artifacts: 1,000+ lines
├─ Configuration: 200 lines
├─ Data files: 800+ lines

Total: ~10,000+ lines of code + documentation
```

---

## NAVIGATION TIPS

### For Reviewers
1. Start with [CODEBASE_EXPLORATION_REPORT.md](CODEBASE_EXPLORATION_REPORT.md) (5 min read)
2. Review [ARCHITECTURE_REFERENCE.md](ARCHITECTURE_REFERENCE.md) (10 min)
3. Check [tantra_integration_test_report.json](tantra_integration_test_report.json) for test results
4. Verify [runtime_hostile_suite.json](runtime_hostile_suite.json) for failure handling

### For Engineers
1. Start with [README.md](README.md) for overview
2. Read [ARCHITECTURE_REFERENCE.md](ARCHITECTURE_REFERENCE.md) data flow section
3. Study [sanskar.py](sanskar.py) + [core.py](core.py) for logic
4. Run `python tantra_integration_self_test.py` to understand flow
5. Check [observability.py](observability.py) for instrumentation

### For Operators
1. Read [OPERATOR_MANUAL.md](OPERATOR_MANUAL.md)
2. Follow [DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md) Scenario 1 (dev deployment)
3. Check [AUTHORITY_MATRIX.md](AUTHORITY_MATRIX.md) for boundaries
4. Monitor [observability.log](observability.log) for health

### For Architects
1. Review [TANTRA_PLACEMENT.md](TANTRA_PLACEMENT.md)
2. Study [AUTHORITY_MATRIX.md](AUTHORITY_MATRIX.md)
3. Review [adapter_layer/canonical_adapter.py](adapter_layer/canonical_adapter.py)
4. Check [governance_runtime_monitor.py](governance_runtime_monitor.py)
5. Plan Phase 1 using [ARCHITECTURE_REFERENCE.md](ARCHITECTURE_REFERENCE.md) "Phase 1 Implementation Dependencies"

---

## STATUS LEGEND

| Symbol | Meaning |
|--------|---------|
| ✅ | Ready, implemented, working |
| ⚠️ | Partially implemented, simulated, or needs work |
| ❌ | Not implemented, planned |
| ← NEW | Created in this exploration session |

---

