# TANTRA SANSKAR - OPERATOR MANUAL

**Version:** Phase 11 (May 28, 2026)  
**Audience:** Incoming developers, operators, SREs  
**Objective:** Zero-knowledge handover to operational readiness

---

## TABLE OF CONTENTS

1. [Quick Start (5 minutes)](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Running the System](#running-the-system)
4. [Observing the System](#observing-the-system)
5. [Common Operations](#common-operations)
6. [Failure Scenarios](#failure-scenarios)
7. [Troubleshooting](#troubleshooting)
8. [Authority Boundaries](#authority-boundaries)
9. [Recovery Procedures](#recovery-procedures)
10. [Escalation Guide](#escalation-guide)

---

## QUICK START

### 30-Second System Startup

```bash


./run.sh --profile development


./health_check.sh


python tantra_integration_harness.py


./shutdown.sh
```

### Expected Output

```
✓ ALL TESTS PASSED (19/19)
  Execution time: 0.02 seconds
```

### What You're Running

- **SANSKAR:** Ranking engine (core logic)
- **RAJYA:** Governance validator (enforces boundaries)
- **Enforcement:** Decision authority (permits/rejects decisions)
- **Bucket:** Truth store (persistent storage)
- **InsightBridge:** Observability (telemetry collection)

---

## ARCHITECTURE OVERVIEW

### The Six-Phase Pipeline

```
Signal Input
    ↓
SANSKAR (ranks items 0-1 scale)
    ↓
RAJYA (validates governance bounds)
    ↓
Enforcement (applies authority decision)
    ↓
Bucket (persists to truth store)
    ↓
InsightBridge (emits telemetry)
    ↓
Output
```

### Key Concepts

#### Trace ID (Immutable)
- **Definition:** Unique identifier for a transaction
- **Behavior:** Created at Signal Input, never changes
- **Use:** Track transaction through all 6 phases
- **Example:** `tr-2026-05-28-001`

#### Signal Lineage
- **Definition:** Append-only log of phases traversed
- **Behavior:** Only grows, never shrinks
- **Use:** Audit trail, replay validation
- **Example:** `["signal_source", "sanskar", "rajya", "enforcement", "bucket", "insight_bridge"]`

#### Governance Boundaries
- **Definition:** Constitutional limits on decision-making
- **Boundary 1:** Confidence ≠ Legitimacy (high confidence ≠ valid)
- **Boundary 2:** Intelligence ≠ Governance (smart ≠ permitted)
- **Boundary 3:** Observability ≠ Authority (seeing ≠ controlling)
- **Boundary 4:** Replay Stability ≠ Permission (repeatable ≠ allowed)

---

## RUNNING THE SYSTEM

### Startup Modes

#### Development (Isolated)
```bash
./run.sh --profile development
```
- Local-only, no external services
- Fast startup/shutdown
- Suitable for: Testing, debugging, demos

#### Integration (With Services)
```bash
./run.sh --profile integration
```
- Connects to RAJYA, Bucket, InsightBridge
- Requires: Other services running on localhost:8001-8003
- Suitable for: Testing multi-component interaction

#### Staging (High Availability)
```bash
./run.sh --profile staging
```
- 3 replicas, SLA enforcement
- Circuit breaker active
- Suitable for: Pre-production validation

#### Production (Locked Down)
```bash
./run.sh --profile production
```
- Immutable config, TLS required
- Audit logging enabled
- Strict SLA enforcement
- Suitable for: Production deployment

### With Custom Configuration

```bash
# Override specific settings
./run.sh --profile development --port 9999 --trace-backend custom-backend

# Environment variables
export SANSKAR_PORT=9999
export SANSKAR_ENV=development
./run.sh
```

### Health Check

```bash
./health_check.sh
```

Output:
```json
{
  "status": "HEALTHY",
  "uptime_seconds": 123,
  "events_processed": 892,
  "governance_violations": 0,
  "observability_lag_ms": 45
}
```

### Graceful Shutdown

```bash
./shutdown.sh
```
- Stops accepting new signals
- Drains in-flight transactions
- Flushes observability buffer
- Persists event log
- Closes gracefully (no data loss)

---

## OBSERVING THE SYSTEM

### Execution Proof

One-command live demonstration:

```bash
python tantra_integration_harness.py
```

Shows:
1. Full chain startup
2. Contract exchange
3. Trace propagation
4. Downstream validation
5. Observability emission
6. Replay registration

Proof file: `live_execution_proof.json`

### Monitoring the Pipeline

#### Check Phase Status
```bash
# SANSKAR processing
cat observability.log | grep "phase:sanskar"

# RAJYA governance checks
cat observability.log | grep "phase:rajya"

# Bucket persistence
cat observability.log | grep "phase:bucket"
```

#### Trace Correlation
```bash
# All events for trace_id: tr-2026-05-28-001
cat observability.log | grep "tr-2026-05-28-001"
```

#### Observability Metrics
```bash
# Latency by phase
grep "phase_latency" observability.log


grep "governance_violation" observability.log


grep "ERROR" observability.log | grep "failure_mode"
```

---

## COMMON OPERATIONS

### Add a New Signal

```python

from sanskar import SANSKAR

engine = SANSKAR()
signal = {
    "signal_id": "sig-custom-001",
    "signal_data": {"metric_1": 45.2, "metric_2": 98.7},
    "origin_metadata": {"source": "my_service", "region": "us-east"}
}

result = engine.process_signal(signal)
print(result)  
```

### Check Governance Status

```bash

curl http://localhost:8000/governance/status


{
  "boundaries_enforced": 4,
  "violations_detected": 0,
  "last_check": "2026-05-28T15:30:00Z"
}
```

### Replay a Transaction

```bash

python -c "
from core import replay_transaction
result = replay_transaction('tr-2026-05-28-001')
print(result)
"
```

### Change Configuration

```bash

export SANSKAR_LOG_LEVEL=DEBUG
./health_check.sh  

export SANSKAR_REPLICAS=5
./shutdown.sh && ./run.sh 
```

---

## FAILURE SCENARIOS

### Scenario 1: RAJYA Timeout

**Symptom:** Transactions stuck at RAJYA phase

**Root Cause:** RAJYA service unresponsive

**Detection:**
```bash

grep "RAJYA.*TIMEOUT" observability.log


```

**Resolution:**
```bash

./run.sh --restart-service rajya


```

### Scenario 2: Governance Violation Detected

**Symptom:** Transactions rejected by RAJYA

**Root Cause:** SANSKAR output violates governance boundaries

**Detection:**
```bash
grep "GOVERNANCE_VIOLATION" observability.log
```

**Example:** AMBIGUOUS confidence state with score 0.99999

**Resolution:**
```bash

cat observability.log | grep "confidence_state:AMBIGUOUS"


python test.py --test-confidence-calculation


./shutdown.sh && ./run.sh
```

### Scenario 3: Bucket Persistence Failed

**Symptom:** Transactions not persisted

**Root Cause:** Bucket storage unavailable

**Detection:**
```bash
grep "BUCKET.*FAILURE" observability.log
```

**Resolution:**
```bash

curl http://localhost:8002/health


./run.sh --restart-service bucket


python -c "from core import retry_pending_persistence; retry_pending_persistence()"


```

### Scenario 4: Observability Degradation

**Symptom:** Telemetry lag exceeds 100ms

**Root Cause:** InsightBridge backlog

**Detection:**
```bash
grep "telemetry_lag_ms" observability.log | tail -10
```

**Resolution:**
```bash

curl http://localhost:8003/queue/status


./run.sh --profile staging  


python -c "from observability import flush_queue; flush_queue()"
```

---

## TROUBLESHOOTING

### System Won't Start

**Check 1: Port Already Bound**
```bash

netstat -an | grep 8000


./run.sh --port 9000
```

**Check 2: Dependency Missing**
```bash

python -m pip list | grep -E "pythonmodule|observability"


pip install -r requirements.txt


./run.sh
```

**Check 3: Permission Denied**
```bash

ls -l ./run.sh ./shutdown.sh


chmod +x ./run.sh ./shutdown.sh ./health_check.sh


./run.sh
```

### High Latency

**Symptom:** Transactions taking >1 second

**Diagnosis:**
```bash

grep "phase_latency_ms" observability.log


grep "phase_latency_ms" observability.log | sort -t: -k3 -n | tail -5
```

**Common Causes & Solutions:**

| Phase | Typical | Slow | Cause | Fix |
|-------|---------|------|-------|-----|
| SANSKAR | 10-50ms | >100ms | Computation overhead | Check input size |
| RAJYA | 5-20ms | >100ms | Governance checks | Verify config |
| Enforcement | 1-5ms | >50ms | Permission check | Review logic |
| Bucket | 20-100ms | >500ms | I/O latency | Check storage |
| InsightBridge | 5-50ms | >200ms | Telemetry backlog | Flush queue |

### Transactions Disagreeing

**Symptom:** Same input produces different output

**Root Cause:** Non-determinism in SANSKAR

**Detection:**
```bash

python -c "
from core import replay_transaction
result1 = replay_transaction('tr-2026-05-28-001')
result2 = replay_transaction('tr-2026-05-28-001')
assert result1 == result2, 'Non-determinism detected!'
print('Determinism verified')
"
```

**Resolution:**
```bash

grep "np.random.seed\|random.seed" core.py


python test.py --test-determinism


```

---

## AUTHORITY BOUNDARIES

### Who Decides What

| Authority | Decides | Cannot Decide |
|-----------|---------|---------------|
| SANSKAR | Ranking scores (0-1) | Whether ranking is permitted |
| RAJYA | Governance conformance | Whether to change governance rules |
| Enforcement | Apply/reject decision | Authority itself |
| Bucket | Persist transaction | What to persist (decided by enforcement) |
| InsightBridge | Emit telemetry | What is "important" (decided by others) |

### Escalation Chain

```
Operator Error
    ↓
Local Restart (./ run.sh)
    ↓
Phase Failure
    ↓
Service Owner (SANSKAR/RAJYA/etc.)
    ↓
Incident Commander
    ↓
Executive Review (if governance violated)
```

---

## RECOVERY PROCEDURES

### Scenario: System Down for 5 Minutes

**Step 1: Determine Duration & Scope**
```bash

grep "HEALTHY" observability.log | tail -1


```

**Step 2: Check for Data Loss**
```bash

python -c "
from event_sourcing import verify_event_log
result = verify_event_log()
print(f'Events: {result[\"count\"]}, Integrity: {result[\"ok\"]}'
"
```

**Step 3: Replay Transactions from Lineage**
```bash

python -c "
from core import find_incomplete_transactions
incomplete = find_incomplete_transactions()
print(f'Found {len(incomplete)} incomplete transactions')
for trace_id in incomplete:
    print(f'Replaying {trace_id}...')
    from core import complete_transaction
    complete_transaction(trace_id)
"
```

**Step 4: Verify Governance**
```bash

curl http://localhost:8000/governance/violations


```

**Step 5: Restore Normal Operations**
```bash

./run.sh


python tantra_integration_harness.py


```

### Scenario: Governance Boundary Violation Detected

**CRITICAL:** Governance violations are integrity breaches

**Step 1: Halt Immediately**
```bash
./shutdown.sh
```

**Step 2: Investigation Mode**
```bash

grep "GOVERNANCE_VIOLATION" observability.log


python -c "
from core import get_transaction_context
ctx = get_transaction_context('tr-VIOLATION-ID')
print(ctx)
"
```

**Step 3: Root Cause Analysis**
- **Question:** Which SANSKAR logic failed?
- **Question:** Was RAJYA check bypassed?
- **Question:** When did code change last?
- **Question:** Who has authority to change governance?

**Step 4: Executive Review Required**
- Do not restart until violation analyzed
- Escalate to Incident Commander
- Document findings

**Step 5: Resolution**
```bash

./run.sh --audit-mode


python tantra_integration_harness.py
```

---

## ESCALATION GUIDE

### Level 1: Recoverable Issue (30 minutes)
- Timeout at single phase
- Observability lag
- Configuration mismatch

**Action:** Restart phase/component

### Level 2: Service Failure (1 hour)
- Bucket storage unavailable
- RAJYA governance engine down
- Network partition

**Action:** Service owner + fallback/failover

### Level 3: Data Integrity Issue (Executive)
- Governance boundary violation
- Non-determinism detected
- Unauthorized decision

**Action:** Halt + Investigation + Review

### Level 4: Architectural Issue (Redesign)
- Recurring governance violations
- Systemic non-determinism
- Authority scope exceeded

**Action:** Architecture review + Governance amendment

---

## QUICK REFERENCE

### Commands

| Command | Purpose |
|---------|---------|
| `./run.sh --profile development` | Start development instance |
| `./health_check.sh` | Verify system health |
| `./shutdown.sh` | Graceful shutdown |
| `python tantra_integration_harness.py` | Full integration test |
| `grep "ERROR" observability.log` | Find errors |

### Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| SANSKAR_PORT | 8000 | Port to listen on |
| SANSKAR_ENV | development | Profile (dev/int/stg/prod) |
| TRACE_BACKEND | stdout | Where to send traces |
| SLA_ENFORCEMENT | disabled | Enable SLA checks |
| GOVERNANCE_LEVEL | strict | Governance enforcement |

### Files

| File | Purpose |
|------|---------|
| `observability.log` | All events/telemetry |
| `event_store.json` | Persisted events |
| `runtime_config/` | Configuration files |
| `integration_contracts/` | Schema definitions |
| `adapter_layer/` | Canonical adapter |

---

## CONCLUSION

This system is designed for:
- ✓ Determinism (same input → same output)
- ✓ Observability (full trace visibility)
- ✓ Governance (boundaries maintained)
- ✓ Operability (clear diagnostics)
- ✓ Recovery (graceful failure handling)

**Key Principle:** If unsure, escalate. Better to be cautious than to violate governance boundaries.

---

**Version:** Phase 11 (May 28, 2026)  
**Status:** Ready for Operational Handover
