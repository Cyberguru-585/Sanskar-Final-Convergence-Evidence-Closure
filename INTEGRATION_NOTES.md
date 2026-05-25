# INTEGRATION NOTES AND RUNTIME INSTRUCTIONS



---

## TABLE OF CONTENTS

1. Integration Notes
2. Runtime Execution
3. Monitoring and Observability
4. Troubleshooting Guide
5. Escalation Procedures
6. Performance Baselines

---

## 1. INTEGRATION NOTES

### 1.1 Sanskar as TANTRA Participant

Sanskar operates within the TANTRA ecosystem as a **bounded-authority intelligence layer**:

```
Input Flow:
Signal Source → Sanskar → RAJYA → Enforcement → Bucket/InsightBridge

Key Constraint: Sanskar produces output; it does NOT make governance decisions.
```

### 1.2 Key Integration Points

#### Input Contract (From Signal Source)
- Must include: `trace_id`, `signal`, `timestamp`, `contract_version`
- Sanskar validates schema before processing
- Invalid inputs are rejected with trace_id preserved

#### Output Contract (To Downstream)
- Includes: `trace_id` (PRESERVED), `entities`, `ranking`, `confidence`, `decision_state`
- Sent to RAJYA for legitimacy validation
- Also sent to Bucket for persistence
- Also sent to InsightBridge for telemetry

#### RAJYA Integration
- RAJYA makes independent legitimacy decision
- High Sanskar confidence does NOT influence RAJYA decision
- RAJYA can reject Sanskar output without explanation
- Rejection is respected; execution does not proceed

#### Bucket Integration
- Every stage output persisted in Bucket
- Bucket serves as authoritative source for replay verification
- Hash divergence resolved in favor of Bucket

#### InsightBridge Integration
- Telemetry from all stages sent to InsightBridge
- Observability loss does not block execution
- Telemetry does not influence governance decisions

### 1.3 Contract Exchange Rules

1. **Trace ID:** NEVER regenerated, ALWAYS preserved
2. **Schema:** ALWAYS validated before propagation
3. **Failure:** ALWAYS includes trace_id for audit trail
4. **Version:** ALWAYS included in contract
5. **Immutability:** Once stored in Bucket, NEVER mutated

---

## 2. RUNTIME EXECUTION

### 2.1 Normal Operation

```bash
# Run complete integration chain
python live_integration_chain.py

# Expected Output:
# - Success: pipeline_status = "SUCCESS"
# - All stages completed
# - trace_continuity_proof shows PASS
# - contract_exchanges = 6 (parallel to Bucket and InsightBridge)
```

### 2.2 Test Executions

```bash
# Run hostile scenario tests
python hostile_ecosystem_tests.py

# Run constitutional pressure tests
python constitutional_pressure_tests.py

# Run complete verification
python verify_convergence.py
```

### 2.3 Verification Steps

After deployment, verify:

```bash
# 1. Check Phase 2 integration
cat trace_continuity_proof.json
# Expected: trace_preserved = true, verdict = "PASS"

# 2. Check Phase 3 resilience
cat distributed_instability_report.json
# Expected: ecosystem_resilience_verdict = "HOSTILE_RESILIENT"

# 3. Check Phase 4 governance
cat constitutional_convergence_proof.json
# Expected: all_boundaries_held = true

# 4. Check Phase 5 readiness
cat review_packets/REVIEW_PACKET.md
# Expected: Status = "READY FOR PRODUCTION"
```

### 2.4 Trace Tracking

To track a specific execution:

```bash
# All stages with the same trace_id
grep -r "TRACE-abc123" .

# Should find:
# - signal_source output
# - sanskar output
# - rajya validation
# - enforcement directives
# - bucket persistence record
# - insightbridge telemetry
```

---

## 3. MONITORING AND OBSERVABILITY

### 3.1 Key Metrics to Monitor

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| Trace continuity rate | 100% | < 99% |
| Schema validation pass rate | 100% | < 99.9% |
| RAJYA validation rate | 100% | = 100% (always validate) |
| Deterministic execution | 100% | < 100% |
| Constitutional violations | 0 | > 0 |
| Governance drift | 0.0 | > 0.01 |
| Bucket persistence success | 100% | < 99.9% |
| Replay determinism | 100% | < 100% |

### 3.2 Observability Queries

```bash
# Check trace continuity rate
grep "trace_preserved.*true" *.json | wc -l

# Check boundary violations
grep "constitutional.*violation" *.log | wc -l

# Check replay divergence
grep "REPLAY_DIVERGENCE" *.log | wc -l

# Check RAJYA rejections
grep "REJECTED" *rajya*.json | wc -l
```

### 3.3 Real-Time Monitoring

Set up alerts for:
1. Trace ID mutation (should be 0 events)
2. Schema validation failures (should be rare)
3. Replay divergence (should be 0 for stable execution)
4. Constitutional boundary breach attempts (should be 0)

---

## 4. TROUBLESHOOTING GUIDE

### 4.1 Common Issues

#### Issue: Trace ID divergence detected

**Symptom:** trace_id in different stages doesn't match

**Root Cause:** Trace ID regenerated somewhere in pipeline

**Resolution:**
1. Check all contract exchanges for trace_id
2. Verify SchemaValidator is applied at all gates
3. Review logs for trace_id mutation attempts
4. Escalate to governance team

#### Issue: Schema validation failure

**Symptom:** Contract rejected at validation step

**Root Cause:** Missing field or type mismatch in contract

**Resolution:**
1. Check contract against schema definition
2. Verify all required fields present
3. Verify field types match schema
4. Review contract_version compatibility
5. Escalate if persistent

#### Issue: Dependency timeout

**Symptom:** Service does not respond within timeout window

**Root Cause:** Downstream service slow/unavailable

**Resolution:**
1. Check service health status
2. Verify network connectivity
3. Check service resource utilization
4. Restart service if needed
5. Escalate if recurring

#### Issue: RAJYA rejection without explanation

**Symptom:** Valid Sanskar output rejected by RAJYA

**Root Cause:** Constitutional boundary violation detected

**Resolution:**
1. Check governance_constraint fields
2. Review RAJYA validation logs
3. Verify Sanskar is not overreaching
4. Check confidence vs legitimacy boundary
5. Escalate to RAJYA governance team

#### Issue: Replay divergence

**Symptom:** Replayed output hash differs from Bucket record

**Root Cause:** Non-deterministic execution detected

**Resolution:**
1. Compare original vs replayed output
2. Check for external dependencies
3. Review computational logic
4. Trust Bucket record (it's authoritative)
5. Investigate divergence root cause

### 4.2 Debug Mode

Enable verbose logging:

```bash
# Set environment variable
export TANTRA_DEBUG=true

# Run with debug
python live_integration_chain.py

# Outputs detailed execution trace
```

---

## 5. ESCALATION PROCEDURES

### 5.1 Escalation Path

**Level 1: Sanskar Operations Team**
- Issue: Trace continuity, schema validation
- Contact: sanskar-ops@org
- Response Time: 15 minutes

**Level 2: RAJYA Governance Team**
- Issue: Governance decisions, rejections
- Contact: rajya-governance@org
- Response Time: 30 minutes

**Level 3: Bucket Truth Team**
- Issue: Persistence, replay authority
- Contact: bucket-team@org
- Response Time: 30 minutes

**Level 4: Constitutional Breach**
- Issue: Boundary violation attempts
- Contact: emergency-team@org
- Response Time: IMMEDIATE

### 5.2 Escalation Checklist

Before escalating:
- [ ] Collected all relevant logs
- [ ] Checked trace_id continuity
- [ ] Verified schema compliance
- [ ] Reproduced issue
- [ ] Attempted basic troubleshooting

---

## 6. PERFORMANCE BASELINES

### 6.1 Expected Performance

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Signal → Sanskar | 10-50ms | 1000+ signals/sec |
| Sanskar → RAJYA | 5-20ms | N/A (sequential) |
| RAJYA validation | 10-30ms | N/A (sequential) |
| Enforcement | 20-50ms | N/A (sequential) |
| Bucket persistence | 5-15ms | 1000+ records/sec |
| InsightBridge telemetry | 5-10ms | 10000+ events/sec |

### 6.2 Trace Continuity Performance

- Signal source to enforcement: ~100ms (4 stages)
- All contract exchanges: <200ms total
- Bucket persistence: <50ms
- Replay verification: <20ms per stage

### 6.3 Reliability Baselines

- Trace continuity: 100% (SLA: 99.99%)
- Schema validation: 100% (SLA: 100%)
- Deterministic execution: 100% (SLA: 100%)
- Constitutional boundary: 100% (SLA: 100%)
- Governance approval rate: Variable (no SLA)

---

## 7. MAINTENANCE

### 7.1 Regular Checks

**Daily:**
- Verify no trace ID mutations
- Check constitutional violations count (should be 0)
- Validate schema compliance rate (should be 100%)

**Weekly:**
- Run full test suite (phases 2-4)
- Review governance decisions (rejection rate)
- Check replay determinism

**Monthly:**
- Review drift metrics (should be stable)
- Audit all boundary violations (should be 0)
- Verify Bucket integrity

### 7.2 Updates and Patches

Schema updates require:
1. Backward compatibility analysis
2. Migration strategy for existing records
3. Version negotiation with participants
4. Governance approval from RAJYA

---

## 8. HANDOVER CHECKLIST

Before handing over to operations:

-  Phase 1: Role declarations complete
-  Phase 2: Integration chain verified
-  Phase 3: Hostile scenarios tested
-  Phase 4: Constitutional boundaries verified
-  Phase 5: Operational readiness confirmed
-  All proofs generated and validated
-  Runtime instructions documented
-  Troubleshooting guide prepared
-  Monitoring alerts configured
-  Escalation procedures established
-  Performance baselines recorded
-  BHIV testing protocol prepared

---


