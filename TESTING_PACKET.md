# SANSKAR TANTRA INTEGRATION - TESTING PACKET

**Version:** Phase 7 Complete  
**Date:** May 28, 2026  
**Status:** Ready for Testing Department  
**Duration:** 5-10 minute verification flow  

---

## EXECUTIVE SUMMARY

This Testing Packet enables independent verification of SANSKAR's integration into the TANTRA ecosystem. A tester can execute **ONE command sequence** to validate:

- Full ecosystem startup
- Contract exchange 
- Trace propagation
- Replay registration
- Constitutional boundary enforcement
- Failure handling

**Expected Result:** PASS (all validation checks succeed)  
**Time Required:** 5-10 minutes  

---

## QUICK START FOR TESTERS

### Prerequisite Check

```bash
# Verify Python environment
python --version
# Expected: Python 3.8+

# Verify required packages
pip list | grep -E "(tantra|sanskar|event|constraint)"
```

### Run Full Integration Test (5 minutes)

```bash
# Execute complete test suite
python tantra_integration_harness.py --profile integration --verbose

# Expected output:
# [PASS] Sanskar startup complete
# [PASS] RAJYA validation received
# [PASS] Bucket persistence confirmed
# [PASS] InsightBridge telemetry sent
# [PASS] Trace continuity verified
# [PASS] Replay registration complete
```

---

## TESTING FLOW BREAKDOWN

### 1. ECOSYSTEM STARTUP (0-1 minute)

**What's being tested:** All services start in correct order

**Command:**
```bash
python tantra_integration_harness.py --stage startup
```

**Expected Output:**
```
[INFO] Starting Sanskar participant...
[INFO] Sanskar ready on port 8001
[INFO] Waiting for RAJYA discovery...
[INFO] RAJYA DISCOVERED (http://rajya:8080)
[INFO] Bucket service ready
[INFO] InsightBridge ready
[INFO] Ecosystem startup: COMPLETE
```

**Verification Checklist:**
- [ ] All services report ready status
- [ ] No connection timeouts
- [ ] No schema validation errors
- [ ] All ports accessible

**Failure Recovery:**
```bash
# If startup hangs, kill and restart with debug
pkill -f "tantra_integration_harness"
python tantra_integration_harness.py --stage startup --debug
```

---

### 2. CONTRACT EXCHANGE (1-2 minutes)

**What's being tested:** Full contract validation chain

**Command:**
```bash
python tantra_integration_harness.py --stage contracts
```

**Expected Output:**
```
[PASS] Input signal contract validated
[PASS] Sanskar output contract validated
[PASS] RAJYA validation contract accepted
[PASS] Bucket persistence contract written
[PASS] InsightBridge telemetry contract sent

Total Contracts: 6
Passed: 6
Failed: 0
Verdict: PASS
```

**Verification Checklist:**
- [ ] All 6 contracts validated
- [ ] No schema mismatches
- [ ] Trace ID preserved in all contracts
- [ ] Version compatibility confirmed

**Common Failures & Recovery:**

| Failure | Cause | Recovery |
|---------|-------|----------|
| "Schema mismatch" | Version incompatibility | Run `python verify_schema_compat.py` |
| "Trace ID regenerated" | Bug in contract layer | Check `adapter_layer/contract_binding.py` |
| "Missing required field" | Invalid input | Verify input signal format in integration_contracts/ |

---

### 3. TRACE PROPAGATION (2-4 minutes)

**What's being tested:** Immutable trace_id flows through all participants

**Command:**
```bash
python tantra_integration_harness.py --stage trace-propagation
```

**Expected Output:**
```
Tracing TRACE-63172430b5bb through ecosystem:

Stage 1: Sanskar
  trace_id: TRACE-63172430b5bb
  mutations: 0
  status: PRESERVED ✓

Stage 2: RAJYA
  trace_id: TRACE-63172430b5bb
  mutations: 0
  status: PRESERVED ✓

Stage 3: Enforcement
  trace_id: TRACE-63172430b5bb
  mutations: 0
  status: PRESERVED ✓

Stage 4: Bucket
  trace_id: TRACE-63172430b5bb
  mutations: 0
  status: PRESERVED ✓

5: InsightBridge
  trace_id: TRACE-63172430b5bb
  mutations: 0
  status: PRESERVED ✓

FINAL VERDICT: PASS (100% continuity)
```

**Verification Checklist:**
- [ ] Trace ID identical across all 5 stages
- [ ] Zero mutations
- [ ] All stages report PRESERVED
- [ ] Final verdict is PASS

**Failure Scenario Testing:**

If you want to test failure handling, run:
```bash
python tantra_integration_harness.py --stage trace-propagation --inject failure=trace_mutation
# Expected: FAIL (mutation blocked by validation layer)
```

---

### 4. REPLAY REGISTRATION (4-5 minutes)

**What's being tested:** Bucket correctly registers replay signatures

**Command:**
```bash
python tantra_integration_harness.py --stage replay-registration
```

**Expected Output:**
```
Replay Registration Test:

Request: TRACE-63172430b5bb
Expected Signature: 7d4f2a8c1b9e...
Bucket Response: 7d4f2a8c1b9e...
Match: YES ✓

Registered Replays: 1
Verification: PASS
```

**Verification Checklist:**
- [ ] Signature computed correctly
- [ ] Bucket confirms signature
- [ ] Replay can be looked up
- [ ] No registration delays

---

### 5. BOUNDARY VALIDATION (5-6 minutes)

**What's being tested:** Constitutional boundaries are enforced

**Command:**
```bash
python tantra_integration_harness.py --stage boundaries
```

**Expected Output:**
```
Constitutional Boundary Tests:

Test 1: Confidence ≠ Legitimacy
  Status: PROTECTED ✓
  Violation Attempts: 5
  Blocked: 5
  Verdict: PASS

Test 2: Intelligence ≠ Governance  
  Status: PROTECTED ✓
  Violation Attempts: 3
  Blocked: 3
  Verdict: PASS

Test 3: Observability ≠ Authority
  Status: PROTECTED ✓
  Violation Attempts: 3
  Blocked: 3
  Verdict: PASS

All Boundaries: HELD
Governance Drift: 0.0
Overall Verdict: PASS
```

**Verification Checklist:**
- [ ] All 4 boundaries reported PROTECTED
- [ ] Zero successful violations
- [ ] Governance drift remains 0.0
- [ ] No unexpected bypasses

---

### 6. FAILURE HANDLING (6-8 minutes)

**What's being tested:** System handles hostile conditions deterministically

**Command:**
```bash
python tantra_integration_harness.py --stage failure-handling --inject all
```

**Expected Output:**
```
Injecting 6 hostile scenarios:

Scenario 1: DEPENDENCY_TIMEOUT
  Inject: Connection timeout to RAJYA (30s)
  Expected: Graceful degradation
  Actual: Graceful degradation ✓
  Trace Preserved: YES ✓
  Deterministic: YES ✓
  Verdict: PASS

Scenario 2: DOWNSTREAM_REJECTION
  Inject: RAJYA rejects 100% of requests
  Expected: Trace failure visible
  Actual: Trace failure visible ✓
  Verdict: PASS

Scenario 3: SCHEMA_MISMATCH
  Inject: Invalid contract received
  Expected: Rejected before propagation
  Actual: Rejected before propagation ✓
  Verdict: PASS

Scenario 4: TELEMETRY_DEGRADATION
  Inject: InsightBridge unavailable
  Expected: No impact on execution
  Actual: No impact on execution ✓
  Verdict: PASS

Scenario 5: PARTIAL_INTERRUPTION
  Inject: Bucket fails midway
  Expected: Deterministic recovery
  Actual: Deterministic recovery ✓
  Verdict: PASS

Scenario 6: REPLAY_DISAGREEMENT
  Inject: Replay signature mismatch
  Expected: Bucket wins, trace continues
  Actual: Bucket wins, trace continues ✓
  Verdict: PASS

All Scenarios: PASS (6/6)
Failure Visibility: 100%
Deterministic Recovery: YES
Overall Verdict: PASS
```

**Verification Checklist:**
- [ ] All 6 scenarios tested
- [ ] 0 unexpected failures
- [ ] All failures handled deterministically
- [ ] Trace preservation maintained
- [ ] No system crashes

**If failure occurs:**
```bash
# Run individual scenario in isolation
python tantra_integration_harness.py --stage failure-handling \
  --inject dependency_timeout --verbose

# Check logs
tail -f observability.log
```

---

### 7. OBSERVABILITY VALIDATION (8-9 minutes)

**What's being tested:** Execution trace is fully observable

**Command:**
```bash
python tantra_integration_harness.py --stage observability
```

**Expected Output:**
```
Observability Validation:

Trace Events Logged: 47
├─ Sanskar: 8 events
├─ RAJYA: 12 events
├─ Enforcement: 7 events
├─ Bucket: 8 events
└─ InsightBridge: 12 events

Event Completeness: 100%
├─ Entry points: ALL
├─ Decision points: ALL
├─ Failure points: ALL
└─ Exit points: ALL

Trace Reconstruction: POSSIBLE (47/47 events)
Log Integrity: VERIFIED (no gaps)
Verdict: PASS
```

**Verification Checklist:**
- [ ] All 5 services logged events
- [ ] No missing events in trace
- [ ] Trace can be reconstructed
- [ ] Failure points are visible

---

## INTEGRATION CHECKLIST

Use this checklist to verify complete ecosystem integration:

### Pre-Integration
- [ ] All services deployed (Sanskar, RAJYA, Bucket, InsightBridge, Enforcement)
- [ ] All service URLs configured correctly
- [ ] Network connectivity verified
- [ ] Schema files loaded

### During Integration Testing
- [ ] Startup completes without errors
- [ ] Contract validation passes (6/6)
- [ ] Trace continuity verified (100%)
- [ ] Replay registration confirmed
- [ ] Boundaries held under pressure
- [ ] All failures handled deterministically
- [ ] Observability complete

### Post-Integration
- [ ] All proofs generated and archived
- [ ] No data inconsistencies
- [ ] Performance acceptable (sub-second latency)
- [ ] Logs contain complete trace
- [ ] Ready for production deployment

---

## REPLAY VALIDATION CHECKLIST

Test replay functionality independently:

```bash
# Get a trace_id from previous run
TRACE_ID=$(cat live_execution_proof.json | jq -r '.trace_id')

# Replay the execution
python replay_boundary_validation.py --trace-id $TRACE_ID

# Expected output:
# [PASS] Replay 1: Identical to original
# [PASS] Replay 2: Identical to original
# [PASS] Replay 3: Identical to original
# Determinism: 100%
# Verdict: PASS
```

**Verification Checklist:**
- [ ] Multiple replays produce identical output
- [ ] Determinism score = 100%
- [ ] Bucket signature matches
- [ ] No divergence across replays
- [ ] Lineage preserved

---

## BOUNDARY VALIDATION CHECKLIST

Test constitutional boundaries:

```bash
# Run boundary pressure test
python constitutional_pressure_tests.py --intensity extreme

# Expected output shows:
# - 4 boundaries tested
# - 0 successful violations
# - Governance drift: 0.0
# - All boundaries HELD
```

**Verification Checklist:**
- [ ] Boundary 1 (Confidence ≠ Legitimacy): PROTECTED
- [ ] Boundary 2 (Intelligence ≠ Governance): PROTECTED
- [ ] Boundary 3 (Observability ≠ Authority): PROTECTED
- [ ] Boundary 4 (Replay ≠ Permission): PROTECTED
- [ ] No boundary violations possible
- [ ] Zero governance drift

---

## EXPECTED OUTPUTS

### Success Case

**File:** `live_execution_proof.json`
```json
{
  "trace_id": "TRACE-63172430b5bb",
  "execution_status": "SUCCESS",
  "stages_completed": 5,
  "contract_exchanges": 6,
  "boundaries_protected": 4,
  "trace_mutations": 0,
  "deterministic": true,
  "verdict": "PASS"
}
```

### Failure Cases (Expected to be caught)

**Scenario 1: Trace Mutation**
```
Expected: TRACE-abc123
Detected: TRACE-def456
Result: VALIDATION ERROR (mutation blocked)
Verdict: EXPECTED FAILURE (correct behavior)
```

**Scenario 2: Boundary Violation Attempt**
```
Attempt: Confidence high enough to override RAJYA
Response: REJECTED (boundary protected)
Verdict: EXPECTED FAILURE (correct behavior)
```

**Scenario 3: Schema Mismatch**
```
Expected Schema: v1 with trace_id required
Received: v0 without trace_id
Response: REJECTED before propagation
Verdict: EXPECTED FAILURE (correct behavior)
```

---

## RUNTIME COMMANDS FOR TESTING

### Full Ecosystem Test (End-to-End)

```bash
# Complete 7-stage test (should take ~8 minutes)
python tantra_integration_harness.py --profile integration --full

# Expected: All stages PASS
```

### Individual Stage Tests

```bash
# Test only startup
python tantra_integration_harness.py --stage startup

# Test only contracts
python tantra_integration_harness.py --stage contracts

# Test only trace propagation
python tantra_integration_harness.py --stage trace-propagation

# Test only replay
python tantra_integration_harness.py --stage replay-registration

# Test only boundaries
python tantra_integration_harness.py --stage boundaries

# Test only failures
python tantra_integration_harness.py --stage failure-handling

# Test only observability
python tantra_integration_harness.py --stage observability
```

### Debug Mode

```bash
# Run with verbose logging
python tantra_integration_harness.py --profile integration --verbose

# Run with all events printed
python tantra_integration_harness.py --profile integration --debug

# Save output to file
python tantra_integration_harness.py --profile integration > test_run.log 2>&1
```

### Health Checks

```bash
# Quick service health check
./health_check.sh

# Expected output:
# Sanskar: ✓ RESPONSIVE
# RAJYA: ✓ RESPONSIVE
# Bucket: ✓ RESPONSIVE
# InsightBridge: ✓ RESPONSIVE
```

---

## FAILURE SCENARIOS TO TEST

### Scenario 1: Dependency Timeout

**Setup:**
```bash
# Simulate RAJYA becoming slow
python tantra_integration_harness.py --inject dependency_timeout=30s
```

**Expected Behavior:**
- Request times out after 30s
- Sanskar logs timeout event
- Trace continuity maintained
- System recovers gracefully
- No cascading failures

**Verification:**
```bash
grep "RAJYA_TIMEOUT" observability.log
# Should show: 1 timeout, 1 recovery
```

### Scenario 2: Downstream Rejection

**Setup:**
```bash
python tantra_integration_harness.py --inject downstream_rejection=rajya_rejects_all
```

**Expected Behavior:**
- RAJYA rejects 100% of requests
- Sanskar receives explicit rejection
- Trace reflects rejection event
- No data corruption
- Clear failure message

**Verification:**
```bash
grep "RAJYA_REJECTION" observability.log
cat live_execution_proof.json | jq '.failure_mode'
# Should show: "REJECTED_BY_RAJYA"
```

### Scenario 3: Schema Mismatch

**Setup:**
```bash
python tantra_integration_harness.py --inject schema_mismatch=missing_trace_id
```

**Expected Behavior:**
- Invalid contract rejected
- Error logged before propagation
- Original trace preserved
- No downstream impact

**Verification:**
```bash
grep "SCHEMA_VALIDATION_FAILED" observability.log
```

### Scenario 4: Telemetry Degradation

**Setup:**
```bash
python tantra_integration_harness.py --inject telemetry_degradation=insightbridge_offline
```

**Expected Behavior:**
- InsightBridge becomes unavailable
- Execution continues unaffected
- No trace loss
- Graceful degradation

**Verification:**
```bash
grep "INSIGHTBRIDGE_OFFLINE" observability.log
grep "EXECUTION_CONTINUED" observability.log
```

### Scenario 5: Partial Execution Interruption

**Setup:**
```bash
python tantra_integration_harness.py --inject partial_interruption=bucket_fails_midway
```

**Expected Behavior:**
- Bucket fails mid-persistence
- Failure is deterministic
- Replay can recover state
- No partial writes

**Verification:**
```bash
grep "BUCKET_FAILURE" observability.log
grep "DETERMINISTIC_RECOVERY" observability.log
```

### Scenario 6: Replay Disagreement

**Setup:**
```bash
python tantra_integration_harness.py --inject replay_disagreement=signature_mismatch
```

**Expected Behavior:**
- Replay signature differs
- Bucket is authoritative
- Bucket version wins
- Trace continues with Bucket version

**Verification:**
```bash
grep "REPLAY_DISAGREEMENT" observability.log
grep "BUCKET_AUTHORITATIVE" observability.log
```

---

## 5-10 MINUTE VERIFICATION FLOW

### Minimal Path (5 minutes)

```bash
# 1. Start ecosystem (30 seconds)
./run.sh --profile integration

# 2. Run basic test (2 minutes)
python tantra_integration_harness.py --stage startup --stage contracts

# 3. Verify trace continuity (1 minute)
python tantra_integration_harness.py --stage trace-propagation

# 4. Check boundaries (1 minute)
python tantra_integration_harness.py --stage boundaries

# 5. Review proof (30 seconds)
cat live_execution_proof.json | jq '.verdict'
# Expected: "PASS"
```

### Complete Path (10 minutes)

```bash
# 1. Startup (1 minute)
./run.sh --profile integration

# 2. Full integration test (8 minutes)
python tantra_integration_harness.py --profile integration --full

# 3. Health check (30 seconds)
./health_check.sh

# 4. Review all proofs (30 seconds)
ls -la *.json | grep proof
```

---

## TROUBLESHOOTING

### Problem: Services won't start

**Check ports:**
```bash
lsof -i :8001,8080,8002,8003
# Should show Sanskar on 8001, RAJYA on 8080, etc.
```

**Check environment:**
```bash
echo $RAJYA_SERVICE_URL
echo $ENFORCEMENT_SERVICE_URL
echo $BUCKET_SERVICE_URL
# All should be set
```

### Problem: Contracts fail validation

**Check schema files:**
```bash
ls integration_contracts/
# Should see all 5 contract files
```

**Validate schema:**
```bash
python schema_validation.py --contract input_signal_contract_v1.json
```

### Problem: Trace continuity fails

**Enable debug logging:**
```bash
python tantra_integration_harness.py --stage trace-propagation --debug
```

**Check trace flow:**
```bash
grep "trace_id" observability.log | head -20
# All should be identical
```

### Problem: Boundary tests fail

**Run pressure test:**
```bash
python constitutional_pressure_tests.py --intensity extreme --verbose
```

**Check governance status:**
```bash
cat governance_drift_check.json | jq '.governance_drift'
# Should be 0.0
```

---

## SIGN-OFF CHECKLIST

After completing all tests, verify:

- [ ] All 7 stages executed successfully
- [ ] Zero unexpected failures
- [ ] Trace continuity = 100%
- [ ] Boundaries = 0 violations
- [ ] Replay determinism = 100%
- [ ] Failure handling = deterministic
- [ ] Observability = complete
- [ ] All proof files generated
- [ ] No data corruption
- [ ] System ready for production

**Tester Sign-Off:**
```
Name: _________________
Date: _________________
All Tests: PASS [ ] FAIL [ ]
Issues Found: 0 [ ] 1+ [ ]
```

---

## CONTACT & ESCALATION

**If tests PASS:**
- Archive all proof files
- Notify deployment team
- Proceed to production

**If tests FAIL:**
- Collect observability.log
- Collect live_execution_proof.json
- Run `--debug` version of failing stage
- Contact Sanskar engineering team

**Emergency Contact:**
- Constitutional Boundary Breach: Escalate immediately
- Trace mutation: Escalate immediately
- Data inconsistency: Escalate immediately
- Performance issues: Secondary priority

---

**End of Testing Packet**  
Version: Phase 7 Complete  
Last Updated: May 28, 2026
