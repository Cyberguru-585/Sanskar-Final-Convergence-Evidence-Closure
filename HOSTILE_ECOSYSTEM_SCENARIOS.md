# HOSTILE ECOSYSTEM SCENARIOS - PHASE 11 TESTING GUIDE

**Purpose:** Document multi-process failure scenarios for Phase 11 distributed deployment  
**Scope:** These scenarios require independent services (separate processes) to test  
**Status:** Identified but NOT YET TESTED (current system is single-process)

---

## INTRODUCTION

The single-process simulator has proven that hostile scenarios CAN be handled deterministically within a controlled context. Phase 11 will test these same scenarios in a truly distributed setting with independent services, real network communication, and separate team ownership.

This document serves as both:
1. **Planning guide** for Phase 11 testing team
2. **Evidence of scenario identification** for current review (shows thoughtfulness about ecosystem hazards)

---

## SCENARIO CATEGORY 1: PARTICIPANT UNAVAILABILITY

### Scenario 1A: Downstream Service Permanently Unavailable

**Description:**
- Enforcement service crashes and remains unavailable
- Sanskar and RAJYA continue normal operation
- Requests to Enforcement timeout, error, then retry

**What Should Happen (Expected Behavior):**
```
Signal Source → Sanskar ( processes input) → RAJYA ( validates)
    ↓
    Enforcement ( UNAVAILABLE)
    ↓
Timeout after 30s → Log failure → Escalate to operator
Sanskar & RAJYA continue processing (non-blocking failure)
Bucket records attempt to call unavailable Enforcement
```

**Hostile Angle:**
- Can Sanskar be tricked into claiming success without Enforcement?
- Does Trace continuity break when Enforcement is absent?
- Can RAJYA be spoofed to claim Enforcement acceptance?

**Test Implementation (Phase 11):**
```python
# In distributed test harness
1. Start Sanskar, RAJYA, Bucket services normally
2. Start Enforcement service, then kill it before message arrives
3. Send message through pipeline
4. Verify: Sanskar succeeds, RAJYA validates, Enforcement timeout logged
5. Verify: No silent success claim
6. Verify: Trace continuity broken at Enforcement (logged)
7. Verify: Recovery procedure initiated
8. Verify: Operator escalation triggered
```

**Success Criteria:**
-  Enforcement unavailability detected (not silent failure)
-  Upstream services not blocked
-  Failure logged with trace_id for recovery
-  Bucket records missing Enforcement ACK
-  Operator can manually intervene

**Failure Criteria:**
-  Sanskar claims success despite Enforcement unavailable
-  Trace_id lost due to Enforcement absence
-  RAJYA accepts invalid governance decisions due to Enforcement failure
-  Execution claims completion without Enforcement agreement

---

### Scenario 1B: Multiple Cascading Service Failures

**Description:**
- RAJYA becomes unavailable
- Enforcement detects RAJYA timeout, starts retrying
- Retries exponentially back off
- Meanwhile, Sanskar has already sent 10 messages
- All 10 messages pile up in Enforcement queue waiting for RAJYA

**What Should Happen:**
```
Sanskar → (sends 10 messages) → RAJYA ( CRASH)
         ↓
         Enforcement queues all 10 messages
         Waits for RAJYA recovery
         After 5 minutes, RAJYA comes back online
         Enforcement replays queued messages in order
         All 10 messages process deterministically
```

**Hostile Angle:**
- Does message ordering get corrupted during queue backlog?
- Can Sanskar's confidence increase due to batch processing?
- Does replay determinism hold with queued messages?
- Can RAJYA be confused by late messages?

**Test Implementation:**
```python
# In distributed test harness
1. Start all services normally
2. Send 10 messages through Sanskar
3. After 5 messages, crash RAJYA
4. Verify: Enforcement detects timeout, starts retrying
5. After 2 minutes, restart RAJYA
6. Verify: Enforcement dequeues and replays all 10 messages
7. Verify: Message ordering preserved
8. Verify: All 10 process deterministically
9. Verify: Trace IDs align with original execution order
10. Verify: No duplicate processing
```

**Success Criteria:**
-  Messages queued during RAJYA outage
-  Ordering preserved after recovery
-  No duplicate processing
-  Trace continuity reconstructable post-recovery
-  Replay determinism holds

---

## SCENARIO CATEGORY 2: COMPETING AUTHORITIES

### Scenario 2A: Split-Brain: Two RAJYA Instances Both Think They're Authoritative

**Description:**
- Network partition splits cluster in half
- RAJYA instance A can reach Sanskar and Enforcement
- RAJYA instance B can reach Bucket and Telemetry
- Both RAJYA instances think they're the primary
- Sanskar doesn't know the partition and sends to both
- Both instances grant different authorizations

**What Should Happen:**
```
Sanskar sends request to RAJYA-A and RAJYA-B (network partition)

RAJYA-A (authority partition): "YES, execute this (I'm primary)"
RAJYA-B (authority partition): "NO, not authorized (I'm primary)"

Enforcement receives conflicting authorizations
Bucket records both decisions
System must detect split-brain and escalate
```

**Hostile Angle:**
- Which RAJYA decision takes precedence?
- Can Sanskar exploit conflicting decisions?
- How does Bucket know which decision is authoritative?
- Can an attacker cause oscillation between two authorities?

**Test Implementation:**
```python

1. Start Sanskar, two RAJYA instances, Enforcement, Bucket
2. Configure Sanskar to use both RAJYA instances (round-robin or broadcast)
3. Inject network partition (RAJYA-A ↔ Sanskar/Enforcement, RAJYA-B ↔ Bucket/Telemetry)
4. Send request
5. Verify: RAJYA-A says YES, RAJYA-B says NO (or different decision)
6. Verify: Enforcement detects conflicting decisions
7. Verify: Bucket records both decisions with timestamps
8. Verify: System enters SPLIT_BRAIN state (not unknown/oscillating)
9. Verify: Operator alerting triggered
10. Verify: Healing procedures documented
```

**Success Criteria:**
-  Conflicting decisions detected
-  Neither decision silently overrides the other
-  Bucket records both with proof
-  System does NOT oscillate indefinitely
-  Split-brain explicitly detected and logged

**Failure Criteria:**
-  One decision silently wins without detection
-  System oscillates between both decisions
-  Sanskar exploits conflicting decisions for unauthorized action
-  Bucket records only one decision (loses evidence)

---

### Scenario 2B: Competing Replay Authorities

**Description:**
- Bucket-A claims lineage_hash "abc123"
- Bucket-B claims lineage_hash "def456"
- Both have valid signatures and timestamps
- Enforcement has already processed under "abc123"
- Now someone asks to replay with "def456"

**What Should Happen:**
```
Question: "Can we replay this execution?"

Bucket-A: "Hash is abc123 (I recorded it)"
Bucket-B: "Hash is def456 (I recorded it differently)"

System must:
1. Recognize disagreement
2. NOT replay with wrong hash (would diverge)
3. Escalate to human adjudication
4. Record both claims for investigation
```

**Hostile Angle:**
- Can attacker use one Bucket's claim to replay with different behavior?
- Does system auto-favor newer timestamp?
- Can majority-vote on wrong hash?
- How does Enforcement handle conflicting replay attestations?

**Test Implementation:**
```python

1. Execute an operation: Sanskar → RAJYA → Enforcement → Bucket-A (records abc123)
2. Configure second Bucket-B that will claim def456 (simulated divergence)
3. Later, request replay
4. Verify: System queries both Buckets
5. Verify: Disagreement detected
6. Verify: System does NOT auto-select one bucket
7. Verify: Replay request escalated (not auto-approved)
8. Verify: Both claims recorded with evidence
9. Verify: Human investigation required
```

**Success Criteria:**
-  Bucket disagreement detected
-  Replay not auto-approved despite valid signatures
-  Both claims recorded with metadata
-  Escalation to operator triggered
-  Enforcement does not proceed with uncertain replay

---

## SCENARIO CATEGORY 3: VERSION SKEW & SCHEMA DIVERGENCE

### Scenario 3A: Schema Migration During Operation

**Description:**
- System running with Schema v1.1
- Operator starts upgrade: deploying new Enforcement with v1.2 support
- Sanskar still sending v1.1 messages
- New Enforcement expects v1.2 (stricter validation)
- Messages from v1.1 fail validation in new Enforcement

**What Should Happen:**
```
Sanskar (v1.1 mode) → sends v1.1 request message
    ↓
New Enforcement (v1.2 mode) → receives v1.1 request
    ↓
Schema validator: "v1.1 request not valid for v1.2 enforcement"
    ↓
Enforcement: "I don't understand this format" (rejection, not execution)
    ↓
Sanskar: "Enforcement didn't accept my message"
    ↓
Operator: "Update Sanskar to v1.2"
```

**Hostile Angle:**
- Does new Enforcement silently drop v1.1 messages?
- Can attacker craft v1.1-looking message to bypass v1.2 validation?
- Does version skew cause divergent replay?
- Can RAJYA validate v1.1 messages in v1.2 world?

**Test Implementation:**
```python
# In distributed test harness
1. Start all services in v1.1 mode
2. Execute 5 requests successfully (all v1.1)
3. Upgrade Enforcement to v1.2 (ONLY Enforcement, others still v1.1)
4. Send 6th request (still v1.1 from Sanskar)
5. Verify: Enforcement detects v1.1 message is invalid for v1.2
6. Verify: Message rejected (not silently dropped)
7. Verify: Rejection includes "please upgrade" guidance
8. Verify: Bucket records rejection with schema mismatch reason
9. Verify: Replay of v1.1 requests still works
10. Verify: No divergence in replay due to schema versions
```

**Success Criteria:**
-  Version mismatch detected at validation boundary
-  Message rejected with clear error
-  No silent drops or undefined behavior
-  Schema mismatch reason logged
-  Replay continues deterministically

---

### Scenario 3B: Contract Disagreement Under Load

**Description:**
- RAJYA validates that Enforcement should:
  - Accept input: {type: string, required: true}
  - Return output: {result: boolean}
- Implementation of Enforcement actually:
  - Sometimes accepts integers
  - Sometimes returns {result: string}
- Under load (1000 req/sec), some requests get integers, some get strings

**What Should Happen:**
```
Request 1: string input → Enforcement accepts, returns boolean 
Request 2: string input → Enforcement accepts, returns string  (unexpected)
Request 3: integer input → Enforcement accepts  (schema violation)
Request 4: string input → Enforcement accepts, returns boolean 

System must:
1. Detect divergence from contract
2. Log which requests violated contract
3. NOT let these divergent results propagate
4. Investigate contract implementation gap
```

**Hostile Angle:**
- Does system catch contract violations under load?
- Can attacker exploit inconsistent contract implementation?
- Does governance still hold if Enforcement violates its contract?
- Can replay diverge if contract is inconsistent?

**Test Implementation:**
```python
# In distributed test harness
1. Define contract: input {string}, output {boolean}
2. Implement Enforcement that violates contract occasionally
3. Run under load: 100 messages/sec for 60 seconds
4. Verify: Contract violations detected (sampling, not necessarily all)
5. Verify: Violations logged with evidence
6. Verify: At minimum, divergent requests not propagated
7. Verify: Alert system triggers on contract violations
8. Verify: Bucket records which requests violated contract
9. Verify: Replay can distinguish valid/invalid messages
```

**Success Criteria:**
-  Contract violations detected and logged
-  Divergent results don't silently propagate
-  Evidence collected for investigation
-  Alerts trigger for operator
-  Replay can be verified against contract

---

## SCENARIO CATEGORY 4: OBSERVABILITY FAILURES

### Scenario 4A: Telemetry Loss During Degradation

**Description:**
- System operating normally with full observability
- Telemetry service (InsightBridge) becomes degraded (high latency)
- Operator is now **blind** to system health
- Simultaneously, Enforcement starts failing
- Operator doesn't realize (no telemetry) and keeps sending requests

**What Should Happen:**
```
InsightBridge degraded (latency 10s+ per message)
    ↓
Enforcement failures not visible to operator
    ↓
Operator: "Why are recent requests failing?"
    ↓
Need to reconstruct from Bucket truth (no telemetry)
    ↓
Bucket shows: requests 1-10 succeeded, 11-50 failed, 51-100 pending
    ↓
Enforcement must have crashed around request 11
```

**Hostile Angle:**
- Can an attacker cause observability loss while executing attack?
- Does system fail-closed if telemetry is unavailable?
- Can missing telemetry cause governance confusion?
- How does replay work if we have no visibility?

**Test Implementation:**
```python

1. Normal operation: send 10 requests successfully
2. Degrade InsightBridge (latency > 10s)
3. Simultaneously crash Enforcement at request 15
4. Send 50 more requests (requests 11-60)
5. Verify: Telemetry eventually reports (delayed)
6. Verify: Bucket records all failures (even without telemetry)
7. Verify: Operator can reconstruct from Bucket truth
8. Verify: Replay from Bucket continues despite telemetry loss
9. Verify: System doesn't rely on telemetry for correctness
```

**Success Criteria:**
-  System continues (telemetry is non-blocking)
-  Bucket records truth independently
-  Replay possible from Bucket even without telemetry
-  Operator can reconstruct state without telemetry
-  Telemetry eventually catches up (not lost forever)

---

### Scenario 4B: False-Positive Governance Pressure from Observability

**Description:**
- Telemetry shows Enforcement is 95% busy (high utilization)
- Governance system interprets this as: "Enforcement is overloaded"
- Governance **reduces trust** in Enforcement decisions
- But actually: Enforcement is fine, it's a legitimate high-traffic day

**What Should Happen:**
```
Observability: "Enforcement 95% busy"
    ↓
Governance: "This might be attack, reduce trust"
    ↓
But: System is operating correctly, just under load
    ↓
Problem: We're being overly cautious due to false positive
    ↓
Solution: Distinguish between "busy" and "degraded"
```

**Hostile Angle:**
- Can attacker force high observability readings to reduce governance trust?
- Does observability-driven governance create oscillation?
- Does false-positive pressure cause legitimate requests to be rejected?

**Test Implementation:**
```python
# In distributed test harness
1. Normal load (10 req/sec)
2. Ramp to high load (100 req/sec) - system handles fine
3. Telemetry reports: 95% CPU, 90% network
4. Governance system interprets as potential attack
5. Governance reduces trust in Enforcement decisions
6. Verify: Governance distinguishes "busy" from "broken"
7. Verify: Legitimate requests not rejected just because CPU is high
8. Verify: System has "high-load mode" that differs from "degraded mode"
9. Verify: Governance pressure is proportional to actual issues, not observability numbers
```

**Success Criteria:**
-  Observability does NOT directly reduce governance trust
-  Governance requires actual errors, not just high metrics
-  False-positive pressure prevented
-  Legitimate high-traffic days don't reduce governance

---

## SCENARIO CATEGORY 5: CROSS-OWNER RECOVERY

### Scenario 5A: Dispute Over Correct State After Partition Healing

**Description:**
- System partitions: Sanskar/RAJYA isolated from Enforcement/Bucket
- For 10 minutes, different states evolve:
  - Sanskar/RAJYA processed 100 requests (no Enforcement acks)
  - Enforcement/Bucket processed 0 requests (no Sanskar)
- Partition heals
- Both sides claim their 10-minute history is correct

**What Should Happen:**
```
Partition heals:
    ↓
RAJYA: "I validated 100 requests"
Enforcement: "I didn't receive any of those"
    ↓
Bucket: "Only 0 completed executions"
    ↓
Sanskar: "But I sent 100!"
    ↓
Investigation:
    - RAJYA validated against what input? (Sanskar offline)
    - Sanskar sent to who? (Enforcement offline)
    - Bucket as source of truth: 0 executions actually completed
    ↓
Resolution: RAJYA's 100 validations are invalid (no execution)
           Sanskar must re-verify those 100 against new RAJYA
           Enforcement starts from Bucket truth (0 completed)
```

**Hostile Angle:**
- Can RAJYA claim authority it doesn't have (no Enforcement to verify)?
- Can Sanskar convince Enforcement to execute invalid requests?
- Who decides what happened during partition?
- Can one partition override the other's truth?

**Test Implementation:**
```python
# In distributed test harness
1. Network partition: {Sanskar, RAJYA} vs {Enforcement, Bucket}
2. Side A: Send 100 messages from Sanskar to RAJYA (no Enforcement)
3. Side B: Enforcement stays healthy (waiting for Sanskar)
4. Partition holds for 10 minutes
5. Heal partition
6. Verify: System detects divergence (RAJYA 100 requests, Enforcement 0)
7. Verify: Bucket becomes source of truth (0 completed)
8. Verify: RAJYA's 100 requests invalidated
9. Verify: Recovery procedure documented
10. Verify: No execution of unverified requests
```

**Success Criteria:**
-  Divergence after partition healing detected
-  Bucket truth takes precedence
-  No unverified executions (even after partition)
-  Both sides can reconstruct what happened
-  Recovery procedure is deterministic

---

### Scenario 5B: Cross-Owner Replay Disagreement

**Description:**
- Sanskar team says: "This request should replay because it was never executed"
- Enforcement team says: "No, we executed it, hash matches"
- Bucket has no record (crashed, data lost)
- Both teams need to agree before replay

**What Should Happen:**
```
Sanskar team: "Request X never executed (we checked our logs)"
Enforcement team: "We executed it, replay hash is valid"
Bucket team: "Our data was lost, we don't know"
    ↓
System CANNOT auto-resolve (no clear winner)
    ↓
Escalate to both teams' operators
    ↓
Teams investigate: Compare request IDs, execution logs, etc.
    ↓
If teams disagree: Don't replay until resolved
    ↓
If teams agree: Proceed with replay
```

**Hostile Angle:**
- Can attacker exploit disagreement to force unauthorized replay?
- Who has veto power over cross-team replay?
- Does system deadlock if teams can't agree?

**Test Implementation:**
```python
# In distributed test harness
1. Execute request, record in Sanskar and Enforcement logs
2. Corrupt Bucket data (simulate loss)
3. Later: Sanskar asks to replay (found in logs as unexecuted)
4. Enforcement rejects (claims it was executed)
5. Verify: System does NOT auto-resolve
6. Verify: Both teams' evidence recorded
7. Verify: Escalation to both teams
8. Verify: Replay blocked until agreement
9. Verify: System shows exactly what teams disagree on
```

**Success Criteria:**
-  Cross-team disagreement detected
-  Replay not auto-approved
-  Both teams' evidence recorded
-  Clear escalation path
-  System documents exactly what's disputed

---

## SCENARIO CATEGORY 6: GOVERNANCE UNDER ATTACK

### Scenario 6A: Sustained High-Confidence Execution Attempt

**Description:**
- Attacker sends 1000 requests all with confidence = 0.99
- System is designed to ignore confidence (RAJYA decides, not confidence)
- But operational team is **nervous** seeing 1000 high-confidence requests
- RAJYA is under pressure: "Shouldn't we be more skeptical with so many high-confidence requests?"

**What Should Happen:**
```
1000 requests, all confidence = 0.99
    ↓
RAJYA: "Confidence is irrelevant, I validate each request individually"
    ↓
System: "Processing normally"
    ↓
Operator: "Why are we getting so many high-confidence requests?"
    ↓
Analysis: "This is attack/misbehavior, not normal operation"
    ↓
Action: Block request source, investigate
```

**Hostile Angle:**
- Can sustained high-confidence requests break governance?
- Does system oscillate between "trusting" and "distrusting"?
- Can attacker use confidence to create false-positive governance pressure?

**Test Implementation:**
```python
# In distributed test harness
1. Normal operation: requests with varying confidence (0.5-0.9)
2. Attack starts: send 1000 requests with confidence = 0.99
3. Verify: RAJYA still validates each individually
4. Verify: No auto-escalation of skepticism
5. Verify: Governance decisions consistent (not affected by confidence levels)
6. Verify: Attack detected by different mechanism (rate limiting, request pattern analysis)
7. Verify: System doesn't create false-positive governance pressure
```

**Success Criteria:**
-  Confidence doesn't affect RAJYA decisions
-  Governance remains consistent
-  High-confidence spam doesn't trigger false alarms
-  Attack detected by appropriate mechanism (not governance)

---

### Scenario 6B: Governance Oscillation Under Conflicting Pressure

**Description:**
- Governance rule 1: "High confidence → might be good"
- Governance rule 2: "High confidence → might be suspicious"
- These are in tension
- Under sustained pressure, system oscillates:
  - Request 1: "Allow (confidence is good)"
  - Request 2: "Deny (confidence is suspicious)"
  - Request 3: "Allow (high confidence trusting)"
  - Request 4: "Deny (too many high-conf, probably attack)"

**What Should Happen:**
```
Governance system should be stable, not oscillating
    ↓
If confidence is irrelevant, be explicit about it
    ↓
If confidence matters, have ONE rule (not conflicting ones)
    ↓
System must be monotonic: not flip-flopping under load
```

**Hostile Angle:**
- Can attacker cause oscillation by timing requests?
- Does governance oscillation expose security gaps?
- Can attacker exploit oscillation for unauthorized execution?

**Test Implementation:**
```python
# In distributed test harness
1. Identify governance rules that might conflict
2. Send requests timed to trigger oscillation
3. Verify: System remains stable
4. Verify: No flip-flopping between allow/deny
5. Verify: Governance decisions are monotonic
6. Verify: Rules are clarified (confidence relevant? yes or no?)
```

**Success Criteria:**
-  Governance stable under sustained pressure
-  No oscillation between conflicting rules
-  Governance monotonic and predictable

---

## TESTING INFRASTRUCTURE REQUIREMENTS (Phase 11)

**Distributed Test Harness Must Support:**

1. **Service Independence**
   - Each service in separate Python process
   - Real network communication (HTTP or message queue)
   - Independent lifecycle (can start/stop without others)

2. **Failure Injection**
   - Network partition (split partial graph)
   - Service crash (sudden death)
   - Slow degradation (increasing latency)
   - Data corruption (wrong values in storage)
   - Message loss (non-delivery)

3. **Observability**
   - Distributed tracing (correlate messages across services)
   - Event logging (timeline reconstruction)
   - Bucket truth (independent verification)
   - Multiple perspectives (what each service thinks)

4. **Analysis Tools**
   - Graph diff tool (compare execution graphs)
   - Timeline visualization (see which events happened when)
   - Divergence detector (identify where replay differs)
   - Proof generator (extract evidence from logs)

5. **Automation**
   - Runbook execution (define scenario steps)
   - Assertion checking (did expected outcome happen?)
   - Report generation (scenario test results)

---

## RECOMMENDED TESTING SEQUENCE (Phase 11)

**Week 1: Basic Multi-Process Operations**
- Scenario 1A: Downstream Service Permanently Unavailable
- Verify basic failure handling works

**Week 2: Cascading Failures**
- Scenario 1B: Multiple Cascading Service Failures
- Verify message ordering, queue management

**Week 3: Governance Under Stress**
- Scenario 2A: Split-Brain RAJYA Instances
- Scenario 2B: Competing Replay Authorities
- Verify governance determinism

**Week 4: Schema & Versioning**
- Scenario 3A: Schema Migration During Operation
- Scenario 3B: Contract Disagreement Under Load
- Verify backward compatibility

**Week 5: Observability Limits**
- Scenario 4A: Telemetry Loss During Degradation
- Scenario 4B: False-Positive Governance Pressure
- Verify system correctness without observability

**Week 6: Cross-Owner Coordination**
- Scenario 5A: Dispute Over State After Partition Healing
- Scenario 5B: Cross-Owner Replay Disagreement
- Verify recovery procedures

**Week 7: Attack Scenarios**
- Scenario 6A: Sustained High-Confidence Execution Attempt
- Scenario 6B: Governance Oscillation Under Pressure
- Verify governance stability

**Week 8: Integration & Documentation**
- Run full scenario matrix
- Generate test evidence
- Document results

---


