# FINAL HANDOVER PACKET - SANSKAR
**Date**: 2026-06-12
**From**: Sakshi (SANSKAR Owner)
**To**: Operator (Any developer with zero context)
**Status**: READY FOR INDEPENDENT OPERATION

---

## 1. System Overview

### What is SANSKAR?
SANSKAR is a bounded intelligence subsystem that ranks agricultural regions based on crop yield potential. It operates within the TANTRA ecosystem as a specialized decision component.

### Role in TANTRA
```
Signal (crop data)
  ↓
SANSKAR (ranking intelligence) ← YOU ARE HERE
  ↓
RAJYA (governance review)
  ↓
ENFORCEMENT (action generation)
  ↓
BUCKET (truth storage)
  ↓
InsightBridge (observability)
```

**SANSKAR Responsibility**: Convert input signal (crop data) into ranked recommendations with confidence scores.

**SANSKAR Boundary**: 
- **CAN DO**: Rank regions, score factors, generate confidence metrics
- **CANNOT DO**: Govern decisions, enforce actions, store truth, observe

### Technology Stack
- Language: Python 3.14
- Framework: FastAPI (API server)
- Persistence: Event sourcing (immutable trace log)
- Deployment: Subprocess-based (real process management)

---

## 2. Build State

### Building from Source

**Prerequisites**:
```bash
- Python 3.14+
- pip or conda
- Git
```

**Clone/Install**:
```bash
cd c:\Users\saksh\Downloads\TASK 6
git clone <repo-url>  # or copy files
pip install -r requirements.txt
```

**Key Dependencies**:
- FastAPI (API framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)

**Build Verification**:
```bash
python -m pytest test.py
# All tests should pass
```

### Source Files Critical Path

1. **sanskar.py** - Core ranking logic
2. **core.py** - Decision layer (priority assignment)
3. **runtime_process_manager.py** - Process lifecycle management
4. **api.py** - HTTP API endpoints
5. **event_sourcing.py** - Trace infrastructure

---

## 3. Runtime Map

### Deployment Topology

```
┌─────────────────────────────────────────┐
│         SANSKAR Runtime Stack            │
├─────────────────────────────────────────┤
│  [HTTP API] :8000                       │
│      ↓                                   │
│  [SANSKAR Core Logic]                   │
│      ↓                                   │
│  [Event Sourcing Backend]               │
│      ↓                                   │
│  [Immutable Trace Log] (event_store.json) │
└─────────────────────────────────────────┘
       ↓ upstream
   [Signal Source]
       ↓ downstream
   [RAJYA] (governance)
```

### Starting SANSKAR

**Method 1: Direct Python**
```bash
python sanskar.py
# Starts core logic
```

**Method 2: API Server**
```bash
python api.py
# Starts FastAPI server on localhost:8000
# Endpoints: /signal, /trace, /health
```

**Method 3: Full Chain**
```bash
python full_chain_executor.py
# Executes complete TANTRA chain
```

### Process Management

SANSKAR runs as a real subprocess (not simulated):
- Process: `python sanskar.py` spawned as subprocess
- PID: Real process ID assigned by OS
- Lifetime: Managed by runtime_process_manager.py
- Signal Handling: SIGTERM for graceful shutdown

### Health Checking

**Endpoint**: `GET /health`
```json
{
  "status": "healthy",
  "pid": 318988,
  "uptime_seconds": 42,
  "checks": {
    "process": "OK",
    "trace_infrastructure": "OK",
    "governance": "OK"
  }
}
```

**Expected**: All checks return "OK", status is "healthy"

---

## 4. Authority Map

### Boundaries

```
┌─ SANSKAR ─────────────────┐
│ Input:  Signal (CSV data) │
│ Process: 7-factor ranking │
│ Output: Ranked regions    │
│                           │
│ MAY:                      │
│  • Score regions          │
│  • Rank by score          │
│  • Generate confidence    │
│  • Produce signals        │
│                           │
│ MAY NOT:                  │
│  ✗ Govern decisions       │
│  ✗ Enforce actions        │
│  ✗ Store truth            │
│  ✗ Observe independently  │
│  ✗ Modify governance      │
│  ✗ Override RAJYA         │
└───────────────────────────┘
```

### Authority Validation

Authority violations are **automatically prevented**:

```python
# If SANSKAR tries to write to BUCKET:
if actor != "BUCKET":
    raise AuthorityViolation(f"{actor} cannot write to BUCKET")
```

**Boundary Enforcement Points**:
1. At API endpoint entry (request validation)
2. At stage transition (ownership check)
3. At resource access (ACL check)

### Detecting Violations

**Log Location**: `observability.log`

**Pattern**: Search for "AUTHORITY_VIOLATION"
```bash
grep "AUTHORITY_VIOLATION" observability.log
```

---

## 5. Trace Map

### Reading Traces

**Trace File**: `event_store.json`

**Structure**:
```json
{
  "trace_id": "f170192c-ede5-494b-815f-417958289f60",
  "events": [
    {
      "timestamp": "2026-06-12T07:14:02Z",
      "stage": "SANSKAR",
      "event_type": "ranking_complete",
      "data": {...},
      "hash": "fcfed652afb1...",
      "previous_hash": "a63cee7d63c6..."
    }
  ]
}
```

**Reading via Script**:
```python
import json
with open('event_store.json') as f:
    trace = json.load(f)
for event in trace['events']:
    print(f"{event['timestamp']} {event['event_type']}")
```

### Verifying Trace Integrity

**Trace Hash Chain**:
```bash
python verify_convergence.py
# Verifies: previous_hash matches computed hash of prior event
# Output: TRACE_VALID or TRACE_CORRUPTED
```

**Manual Verification**:
```python
import hashlib, json

# Load trace
trace = json.load(open('event_store.json'))

# For each event
for i, event in enumerate(trace['events']):
    if i > 0:
        prev_event = trace['events'][i-1]
        computed_hash = hashlib.sha256(
            json.dumps(prev_event, sort_keys=True).encode()
        ).hexdigest()
        assert event['previous_hash'] == computed_hash
        print("✅ Event", i, "integrity verified")
```

### Trace Continuity

**Expected Path**:
```
1. Signal received (trace_id generated)
2. SANSKAR processes (ranking output)
3. RAJYA reviews (governance decision)
4. ENFORCEMENT directs (action map)
5. BUCKET stores (merkle hash)
6. InsightBridge observes (event logged)
```

**Verifying Continuity**:
```bash
python verify_convergence.py --check-continuity
# Verifies: trace_id same through all 5 stages
```

---

## 6. Replay Procedure

### Replaying from Stored Trace

**Purpose**: Reconstruct original execution with identical results

**Prerequisites**:
- Original trace stored in `event_store.json`
- Original input signal preserved

**Procedure**:

```bash
# Step 1: Load original execution proof
cat full_chain_execution.json | jq '.stage_outputs.SANSKAR'

# Step 2: Extract input signal
input_signal = json.load(open('full_chain_execution.json'))['stage_outputs']['SANSKAR']

# Step 3: Execute replay
python full_chain_executor.py --replay-mode

# Step 4: Compare output
# Original: ecosystem_convergence_proof.json
# Replay:   (new execution)
# Should be byte-identical
```

### Replay Validation

```bash
python verify_convergence.py --compare-replay
# Output: DETERMINISM_VERIFIED or DIVERGENCE_DETECTED
```

### Expected Outcomes

**Identical Results** ✅:
- Same ranking order
- Same confidence scores
- Same trace_id flow
- Same contract versions

**No Divergence** ✅:
- No random differences
- No floating-point precision errors
- No state leakage between runs

---

## 7. Failure Recovery

### Failure Mode 1: Process Crash

**Symptom**: SANSKAR process exits unexpectedly

**Recovery**:
```bash
# Step 1: Check process status
ps aux | grep sanskar

# Step 2: Review logs
tail -f observability.log

# Step 3: Restart
python runtime_process_manager.py --restart-sanskar

# Step 4: Verify health
curl http://localhost:8000/health
```

### Failure Mode 2: Dependency Unavailable

**Symptom**: RAJYA not responding, request times out

**Recovery**:
```bash
# Step 1: Check RAJYA status
curl http://localhost:8001/health  # RAJYA port

# Step 2: Enable graceful degradation
export GRACEFUL_DEGRADATION=true

# Step 3: Resume SANSKAR
python api.py

# Step 4: SANSKAR queues output, retries when RAJYA recovers
```

### Failure Mode 3: Trace Corruption

**Symptom**: Trace hash chain verification fails

**Recovery**:
```bash
# Step 1: Verify corruption
python verify_convergence.py
# Output: TRACE_CORRUPTED at event #5

# Step 2: Identify last valid event
# Event #4 is last valid

# Step 3: Truncate trace to last valid event
python truncate_trace.py --last-valid-event 4

# Step 4: Re-execute from checkpoint
python replay_from_checkpoint.py --event 4
```

### Failure Mode 4: Authority Violation

**Symptom**: Operation rejected with "AUTHORITY_VIOLATION"

**Recovery**:
```bash
# Step 1: Check operation
grep "AUTHORITY_VIOLATION" observability.log

# Step 2: Verify boundaries
cat authority_violation_proof.json | jq '.authority_matrix'

# Step 3: Confirm operation is legitimate
# If YES: may be boundary definition issue (escalate)
# If NO: operation not permitted by design (do not retry)

# Step 4: If legitimate, escalate to governance team
# Do not attempt to bypass authority
```

---

## 8. File Map

### Directory Structure

```
c:\Users\saksh\Downloads\TASK 6\

├── Core Logic
│   ├── sanskar.py                 - Ranking engine
│   ├── core.py                    - Decision layer
│   ├── enforcement.py             - Action generation
│   └── runtime_adapters.py        - Contract implementations
│
├── Infrastructure
│   ├── api.py                     - HTTP API
│   ├── runtime_process_manager.py - Process lifecycle
│   ├── event_sourcing.py          - Trace backend
│   ├── observability.py           - Logging
│   └── console.py                 - Output formatting
│
├── Execution & Validation
│   ├── full_chain_executor.py     - Full pipeline
│   ├── phase3_replay_validator.py - Replay testing
│   ├── phase4_failure_validator.py- Failure testing
│   ├── phase5_final_audit.py      - Acceptance audit
│   └── verify_convergence.py      - Trace verification
│
├── Proofs & Evidence
│   ├── runtime_boot_proof.json    - Boot evidence
│   ├── runtime_restart_proof.json - Restart evidence
│   ├── service_health_proof.json  - Health evidence
│   ├── ecosystem_convergence_proof.json - Chain evidence
│   ├── full_chain_execution.json  - Execution details
│   ├── trace_reconstruction_proof.json - Lineage
│   ├── runtime_failure_matrix.json - Failure scenarios
│   └── authority_violation_proof.json - Authority
│
└── Documentation
    ├── FINAL_HANDOVER_PACKET.md   - This file
    ├── OPERATOR_RUNBOOK.md        - Procedures
    ├── FINAL_SYSTEM_STATE.md      - Current state
    └── FINAL_ACCEPTANCE_AUDIT.md  - Approval

└── Data
    ├── event_store.json           - Immutable trace log
    ├── crop_yield.csv             - Input signal
    └── observability.log          - Execution logs
```

### Critical Files for Operators

| File | Purpose | Modify? |
|------|---------|---------|
| sanskar.py | Core logic | No - frozen |
| api.py | HTTP API endpoints | No - frozen |
| event_store.json | Trace log | No - immutable |
| observability.log | Logs | Read-only |
| config.yaml | Configuration | Yes - as needed |

---

## 9. Known Debt

### Limitations (Not Bugs)

1. **No External Service Integration** 
   - RAJYA, Bucket, InsightBridge currently mocked
   - Future: Replace with real services
   - Impact: Local testing only

2. **Memory Constraints**
   - Event store in JSON (not database)
   - Single-machine deployment only
   - Future: Distributed event store

3. **No Multi-Region Support**
   - SANSKAR designed for single region at a time
   - Future: Multi-region federation

4. **Manual Recovery Procedures**
   - No auto-recovery for corruption scenarios
   - Future: Automated recovery with consensus

### These Are Not Bugs
- They are known design limitations
- They do not affect Phase 1-5 validation
- They are documented for future phases

---

## 10. Operator FAQ

### Q: How do I know SANSKAR is healthy?
```bash
curl http://localhost:8000/health
```
If all checks return "OK", system is healthy.

### Q: How do I replay an execution?
```bash
python full_chain_executor.py --replay-mode
# Then compare with previous execution
```

### Q: What if I see "AUTHORITY_VIOLATION" in logs?
This is **expected and correct**. SANSKAR is preventing a boundary violation.
Do not attempt to bypass it. Escalate to governance team.

### Q: How do I verify trace integrity?
```bash
python verify_convergence.py
```
All hashes should verify successfully.

### Q: What does "SANSKAR MAY NOT govern" mean?
SANSKAR cannot make governance decisions. It only ranks regions.
RAJYA makes the governance decision based on SANSKAR ranking.

### Q: How do I start fresh (reset state)?
```bash
rm event_store.json
python api.py
```
New execution will start with clean trace.

### Q: Can I modify the ranking factors?
Yes, in sanskar.py, modify FACTORS dict:
```python
FACTORS = {
    "rainfall": 0.15,      # Modify weights here
    "temperature": 0.12,
    ...
}
```
Then restart SANSKAR.

### Q: What if trace_id is not propagating?
Check that all stages are running and connected:
```bash
curl http://localhost:8000/health  # SANSKAR
curl http://localhost:8001/health  # RAJYA (if available)
```

### Q: How long does a full execution take?
Expected: 6-10 ms end-to-end
If slower, check observability.log for bottlenecks

### Q: Where are the logs?
Primary: `observability.log`
Secondary: Console stdout when running api.py

---

## 11. Final Acceptance Status

### Approval Summary

 **TMS (TANTRA Management System)**: APPROVED
- Placement correct
- Convergence complete
- Ecosystem role clear

 **GC (Governance Compliance)**: APPROVED
- Authority bounded
- Governance drift absent
- Negative authority explicit

 **MDU (Metadata & Determinism Unit)**: APPROVED
- Trace complete
- Replay complete  
- Schema discipline complete

### Sign-Off

**Date**: 2026-06-12
**Status**: READY FOR INDEPENDENT OPERATION
**Builder Dependency**: REMOVED

---

## Operator Checklist

Before operating independently, verify:

- [ ] Can start SANSKAR (python api.py)
- [ ] Can access /health endpoint
- [ ] Can read event_store.json
- [ ] Can identify authority boundaries
- [ ] Can replay an execution
- [ ] Can verify trace integrity
- [ ] Can recover from failures (using procedures above)
- [ ] Understand known limitations
- [ ] Have access to this handover packet

---

## Support & Escalation

### Issues with Known Procedures
- Follow failure recovery procedures (Section 7)
- Check observability.log for details
- Verify configuration matches documentation

### Unexpected Errors
- Document the error
- Collect logs (observability.log)
- Report to governance team with context

### Changes to Authority Boundaries
- Submit change request to GC
- Requires re-validation
- Do not modify authority matrix independently

---

**End of Handover Packet**

This packet removes the builder dependency. You can now operate SANSKAR independently.

