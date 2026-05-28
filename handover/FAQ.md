# TANTRA SANSKAR - FREQUENTLY ASKED QUESTIONS

**Version:** Phase 11 (May 28, 2026)  
**Quick Answers for Operators, Developers, Architects**

---

## TABLE OF CONTENTS

1. [General Questions](#general-questions)
2. [Runtime Questions](#runtime-questions)
3. [Integration Questions](#integration-questions)
4. [Governance Questions](#governance-questions)
5. [Failure & Recovery](#failure--recovery)
6. [Performance & Tuning](#performance--tuning)
7. [Advanced Topics](#advanced-topics)

---

## GENERAL QUESTIONS

### Q: What is SANSKAR?

**A:** SANSKAR is a deterministic ranking engine that:
- Takes input signals (data points)
- Produces ranked decisions (0-1 confidence scores)
- Integrates with TANTRA ecosystem (RAJYA, Bucket, InsightBridge)
- Maintains governance boundaries (no violations permitted)
- Provides full observability (trace every transaction)

**Key Point:** Not a machine learning black box. Deterministic + Transparent + Governed.

---

### Q: How is SANSKAR different from other ranking systems?

**A:** 
| Aspect | SANSKAR | Traditional | ML-Based |
|--------|---------|------------|----------|
| Determinism | Always same output for same input | Usually | No |
| Governance | Hard boundaries enforced | Soft guidelines | None |
| Trace | Complete lineage | Partial logs | Black box |
| Replaying | Bit-for-bit identical | Approximate | Non-deterministic |
| Authority | Clear decision makers | Unclear | Hidden weights |

---

### Q: Who owns SANSKAR?

**A:** SANSKAR operates within authority boundaries:
- **SANSKAR** owns ranking logic
- **RAJYA** owns governance validation
- **Enforcement** owns apply/reject decision
- **Bucket** owns persistence
- **InsightBridge** owns observability

No single entity has absolute authority (by design).

---

### Q: How much does SANSKAR cost?

**A:** Resource requirements:
- **CPU:** 1-2 cores (scaling linearly with throughput)
- **Memory:** 512MB - 2GB (depends on cache size)
- **Storage:** ~1MB per 1000 transactions (event log)
- **Network:** ~10KB per transaction (observability)

Typical: **Small deployment ~ $100/month cloud cost**

---

### Q: Can SANSKAR handle my use case?

**A:** SANSKAR is suitable for:
- ✓ Deterministic decision-making
- ✓ High governance requirements
- ✓ Full auditability needed
- ✓ Replaying transactions required

SANSKAR is NOT suitable for:
- ✗ Non-deterministic algorithms
- ✗ Real-time machine learning
- ✗ Streaming analytics (limited replay)
- ✗ Black-box decision systems

---

## RUNTIME QUESTIONS

### Q: How do I start the system?

**A:** One command:
```bash
./run.sh --profile development
```

Or with custom settings:
```bash
./run.sh --profile production --port 9000 --replicas 3
```

Expected startup time: < 1 second

---

### Q: Why is my system taking 30 seconds to start?

**A:** Likely causes:
1. **Waiting for dependencies:** RAJYA/Bucket/InsightBridge not ready
   - **Fix:** Start them first, or use `--profile development` (no deps)
2. **Port conflicts:** Another process using port 8000
   - **Fix:** `./run.sh --port 9000`
3. **Slow storage:** Event log recovery is slow
   - **Fix:** Delete old `event_store.json` and restart

**Debug:**
```bash
./run.sh --profile development --log-level DEBUG
```

---

### Q: How do I know if SANSKAR is healthy?

**A:** Run health check:
```bash
./health_check.sh
```

Expected output:
```json
{
  "status": "HEALTHY",
  "uptime_seconds": 123,
  "events_processed": 892,
  "governance_violations": 0,
  "observability_lag_ms": 45
}
```

**Key metrics:**
- `status == "HEALTHY"` ✓
- `governance_violations == 0` ✓
- `observability_lag_ms < 100` ✓

---

### Q: What's the difference between profiles?

**A:**
| Profile | Use Case | Dependencies | Performance |
|---------|----------|--------------|-------------|
| **development** | Local testing | None | Fast (in-memory) |
| **integration** | Multi-component tests | RAJYA, Bucket, Bridge | Normal |
| **staging** | Pre-production | All services + HA | Scaled (3 replicas) |
| **production** | Live traffic | All services, locked | SLA-enforced |

---

### Q: Can I change configuration without restarting?

**A:** Depends on the setting:

**No restart needed:**
- Log level (`--log-level DEBUG`)
- Trace backend (`--trace-backend`)
- Observability settings

**Restart required:**
- Port (`--port`)
- Number of replicas (`--replicas`)
- Governance level
- Storage backend

**To change restart-required settings:**
```bash
./shutdown.sh
./run.sh --profile production --replicas 5  # New setting
```

---

### Q: How do I stop the system safely?

**A:**
```bash
./shutdown.sh
```

What happens:
1. Stops accepting new signals
2. Drains in-flight transactions (waits up to 30 seconds)
3. Flushes observability buffer
4. Persists event log
5. Closes gracefully

**Worst case:** Ctrl+C (transactions may lose in-flight state, but persisted ones are safe)

---

## INTEGRATION QUESTIONS

### Q: How do I send a signal to SANSKAR?

**A:**

**Option 1: Python API**
```python
from sanskar import SANSKAR

engine = SANSKAR()
signal = {
    "signal_id": "sig-001",
    "signal_data": {"metric_1": 45.2, "metric_2": 98.7},
    "origin_metadata": {"source": "my_system", "region": "us-east"}
}
result = engine.process_signal(signal)
print(result["rankings"])  # Ranking output
```

**Option 2: HTTP API**
```bash
curl -X POST http://localhost:8000/process_signal \
  -H "Content-Type: application/json" \
  -d '{
    "signal_id": "sig-001",
    "signal_data": {"metric_1": 45.2}
  }'
```

**Option 3: Async Event**
```python
from event_sourcing import emit_signal_event
emit_signal_event({
    "signal_id": "sig-001",
    "signal_data": {"metric_1": 45.2}
})
```

---

### Q: What's the contract format?

**A:** Contracts are versioned JSON schemas:

**Input (Signal Source):**
```json
{
  "signal_id": "sig-2026-05-28-001",
  "timestamp": "2026-05-28T15:30:00Z",
  "signal_data": {"metric_1": 45.2, "metric_2": 98.7},
  "origin_metadata": {"source": "weather_station"}
}
```

**Output (After SANSKAR):**
```json
{
  "trace_id": "tr-2026-05-28-001",
  "rankings": [
    {"item": "option_a", "score": 0.78, "rank": 1},
    {"item": "option_b", "score": 0.65, "rank": 2}
  ],
  "confidence_state": "CONFIDENT"
}
```

**After RAJYA:**
```json
{
  "trace_id": "tr-2026-05-28-001",
  "governance_check": {"status": "passed", "violations": []},
  "validated_at": "2026-05-28T15:30:02Z"
}
```

See: `integration_contracts/` for all schemas

---

### Q: Can I add a custom phase to the pipeline?

**A:** Technically yes, but:

**Before you add a phase:**
1. Does RAJYA governance need to validate it?
2. Is it aligned with existing boundaries?
3. Does it emit observability events?
4. Can transactions replay through it deterministically?

**How to add:**
1. Define schema in `integration_contracts/`
2. Create adapter in `adapter_layer/`
3. Register in `canonical_adapter.py`
4. Test with `ecosystem_instability_suite.py`
5. Update authority map in handover/

**Warning:** Wrong phase ordering = governance violations

---

### Q: How do I test integration without deploying?

**A:** Use the harness:
```bash
python tantra_integration_harness.py
```

This:
- Starts all phases
- Sends test signal
- Validates contracts at each boundary
- Checks trace immutability
- Emits observability
- Validates replay

**Expected:** 19/19 tests pass in < 0.05 seconds

---

## GOVERNANCE QUESTIONS

### Q: What are governance boundaries?

**A:** Four constitutional boundaries:

**1. Confidence ≠ Legitimacy**
- High confidence ≠ valid decision
- Example: AMBIGUOUS state cannot have confidence = 0.99999
- Enforcer: RAJYA

**2. Intelligence ≠ Governance**
- Smart algorithm ≠ permitted decision
- Example: Algorithm result must pass governance check
- Enforcer: RAJYA

**3. Observability ≠ Authority**
- Seeing something ≠ controlling it
- Example: InsightBridge emits telemetry but cannot override decisions
- Enforcer: Enforcement layer

**4. Replay Stability ≠ Permission**
- Reproducible ≠ allowed
- Example: Old transaction cannot be replayed if now invalid
- Enforcer: Bucket + validation

---

### Q: What happens if a boundary is violated?

**A:** 
1. **Detection:** Happens at RAJYA (governance validator)
2. **Response:** Automatic rejection
3. **Logging:** Full transaction context logged
4. **Action:** Escalation to Incident Commander
5. **Resolution:** Investigation + governance amendment (if rule wrong)

**Example:**
```
Input: AMBIGUOUS confidence with score 0.99999
RAJYA: ✗ REJECT "Boundary 1 violation: Confidence ≠ Legitimacy"
Output: Error returned, transaction halted
```

---

### Q: Who has authority to change governance boundaries?

**A:** 
- **NOT SANSKAR:** Cannot modify boundaries
- **NOT RAJYA:** Can only validate, not modify
- **NOT Enforcement:** Can apply existing rules, not change them
- **YES Executive/Board:** Must amend governance charter

**Process:**
1. Proposal to change boundary
2. Executive review
3. Constitutional amendment vote
4. Code change + deployment
5. All-system regression test

---

### Q: What's the difference between a rejection and a failure?

**A:**
| Type | Cause | Recoverable | Action |
|------|-------|-------------|--------|
| **Rejection** | Boundary violated | Modify input, retry | Return error |
| **Timeout** | Service slow | Retry with backoff | Circuit breaker |
| **Failure** | System error | Depends | Restart/investigate |
| **Governance Violation** | Boundary crossed | Investigation required | Halt + escalate |

---

## FAILURE & RECOVERY

### Q: SANSKAR timed out, what do I do?

**A:**
```bash
# 1. Check health
./health_check.sh

# 2. If unhealthy, restart
./shutdown.sh && ./run.sh

# 3. Run integration test
python tantra_integration_harness.py

# 4. Replay pending transactions
python -c "from core import retry_pending_transactions; retry_pending_transactions()"
```

**If still timing out:**
- Check CPU/memory usage
- Increase replicas: `./run.sh --profile staging`
- Contact SRE team

---

### Q: I got a governance violation error. What now?

**A:** DO NOT RESTART YET.

```bash

grep "GOVERNANCE_VIOLATION" observability.log > violation_report.txt


python -c "from core import get_violation_context; print(get_violation_context())" > context.json


./shutdown.sh 
./run.sh --audit-mode  
python tantra_integration_harness.py  
```

---

### Q: How do I replay a transaction?

**A:**
```bash

python -c "
from core import replay_transaction
result = replay_transaction('tr-2026-05-28-001')
print(f'Replayed successfully: {result}')
"


python -c "
from core import verify_replay_determinism
assert verify_replay_determinism('tr-2026-05-28-001')
print('✓ Replay is deterministic')
"
```

**Key Point:** Replay must produce IDENTICAL output (bit-for-bit). If different, investigate non-determinism.

---

### Q: What data do I lose if SANSKAR crashes?

**A:** **Nothing** (with proper shutdown).

Persisted:
- ✓ Event log (`event_store.json`)
- ✓ Completed transactions (in Bucket)
- ✓ Observability events (in InsightBridge)

In-flight:
- ✗ Transactions between phases (lost, can be replayed)
- ✗ In-memory cache (regenerated from event log)

**Recovery:**
```bash
./run.sh  
```

---

## PERFORMANCE & TUNING

### Q: SANSKAR is slow, what can I do?

**A:**

**Step 1: Identify bottleneck**
```bash
grep "phase_latency_ms" observability.log | sort -t: -k3 -n | tail -5
```

**Step 2: Optimize by phase**

**If SANSKAR slow:**
- Check input size (large signal_data?)
- Check ranking algorithm complexity
- Profile CPU usage
- Fix: Optimize ranking logic or shard inputs

**If RAJYA slow:**
- Check number of governance rules
- Check if I/O happening (shouldn't be)
- Fix: Cache governance checks, parallelize

**If Bucket slow:**
- Check storage latency (I/O)
- Check if network (remote storage?)
- Fix: Use local SSD or reduce replica count

**If InsightBridge slow:**
- Check telemetry backlog size
- Check if network congested
- Fix: Reduce telemetry detail or scale telemetry workers

**Step 3: Scale horizontally**
```bash
./run.sh --profile staging --replicas 5
```

---

### Q: How much data can SANSKAR handle?

**A:**

| Metric | Capacity | Bottleneck |
|--------|----------|-----------|
| Signals/second | 1,000-10,000 | CPU (SANSKAR ranking) |
| Transactions in flight | 10,000-100,000 | Memory |
| Events stored | 1,000,000+ | Storage (but not all kept hot) |
| Concurrent processes | 3-10 | OS file descriptor limits |

**Scaling approach:**
- Replicate SANSKAR (multiple ranking instances)
- Use Bucket replicas (3-5 for durability)
- Shard event log (older events archive)

---

### Q: Should I cache transaction results?

**A:** 

**Caching is safe if:**
- Same input always produces same output (determinism guarantee)
- Cache is invalidated on code deploy
- Cache is transparent (for debugging)

**Example:**
```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def cached_process_signal(signal_id):
    # Cache hit rate typically 30-50%
    return process_signal(signal_id)
```

**Cost-benefit:**
- Pros: 10-100x latency improvement
- Cons: 1-10MB memory overhead
- Break-even: > 100 req/sec

---

## ADVANCED TOPICS

### Q: How do I implement a custom SANSKAR algorithm?

**A:**
1. Implement `RankingAlgorithm` interface
2. Update `core.py` - `calculate_ranking()` method
3. Test determinism: `python test.py --test-determinism`
4. Test governance: `python test.py --test-governance`
5. Deploy with version bump

**Template:**
```python
class CustomRankingAlgorithm:
    def calculate_ranking(self, signal_data: Dict) -> List[Dict]:
        # Must be deterministic (no random, same seed)
        # Must return scores 0-1
        # Must handle all input types
        rankings = []
        for item, value in signal_data.items():
            score = self._normalize_score(value)
            rankings.append({"item": item, "score": score})
        return sorted(rankings, key=lambda x: -x["score"])
    
    def _normalize_score(self, value):
        # Deterministic normalization
        return (value % 1.0)  # Example
```

---

### Q: Can I deploy multiple versions of SANSKAR?

**A:** Yes, with canary deployment:

```bash

./run.sh --profile production --version v1 --replicas 8


./run.sh --profile production --version v2 --replicas 1 --traffic-weight 0.1


grep "version:v2" observability.log | grep "ERROR" | wc -l


./shutdown.sh --version v2


./run.sh --profile production --version v2 --replicas 9
```

---

### Q: How do I debug a non-determinism issue?

**A:**

```bash

python -c "
from core import detect_non_determinism
issues = detect_non_determinism()
if issues:
    print(f'Non-determinism detected: {issues}')
    for issue in issues:
        print(f'  - {issue[\"trace_id\"]}: {issue[\"difference\"]}')
"


python -c "
from core import analyze_transaction_determinism
analysis = analyze_transaction_determinism('tr-problematic-id')
print(f'Input: {analysis[\"input\"]}')
print(f'Run 1 Output: {analysis[\"output_1\"]}')
print(f'Run 2 Output: {analysis[\"output_2\"]}')
print(f'Difference: {analysis[\"diff\"]}')
print(f'Root Cause: {analysis[\"probable_cause\"]}')
"
```

**Common causes:**
1. **Random number without seed** → Fix: Use `random.seed(hash(trace_id))`
2. **Dict iteration (unordered)** → Fix: Use `OrderedDict`
3. **Floating point precision** → Fix: Round to N decimal places
4. **Timing-dependent logic** → Fix: Use external timestamp

---

### Q: How do I contribute a fix or improvement?

**A:**
1. Create feature branch: `git checkout -b feature/my-improvement`
2. Make changes, test locally: `python test.py --test-all`
3. Run integration: `python tantra_integration_harness.py`
4. Push branch: `git push origin feature/my-improvement`
5. Create pull request with:
   - Description of change
   - Test results
   - Governance impact (if any)
   - Performance impact (if any)
6. Peer review by 2 maintainers
7. Merge after approval

---

### Q: Where can I learn more?

**A:**

**Architecture:**
- [INTEGRATION_NOTES.md](../INTEGRATION_NOTES.md)
- [DEPLOYMENT_READINESS.md](../DEPLOYMENT_READINESS.md)

**Operations:**
- [operator_manual.md](../handover/operator_manual.md)
- [authority_boundary_map.md](../handover/authority_boundary_map.md)

**Technical Specs:**
- [adapter_layer/canonical_adapter.py](../adapter_layer/canonical_adapter.py)
- [adapter_layer/contract_registry.json](../adapter_layer/contract_registry.json)

**Proofs:**
- [runtime_boot_proof.json](../runtime_boot_proof.json)
- [cross_ecosystem_replay_proof.json](../cross_ecosystem_replay_proof.json)
- [ecosystem_failure_report.json](../ecosystem_failure_report.json)

---

## STILL HAVE QUESTIONS?

**Contact:**
- **Technical Issues:** SRE team (sre@company)
- **Governance Questions:** Incident Commander (ic@company)
- **Architecture Decisions:** TANTRA governance board (board@company)

---

**Version:** Phase 11 (May 28, 2026)  
**Status:** Ready for Operational Support
