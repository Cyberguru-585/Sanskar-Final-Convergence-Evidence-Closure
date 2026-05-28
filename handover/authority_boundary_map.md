# AUTHORITY BOUNDARY MAP

**Version:** Phase 11 (May 28, 2026)  
**Purpose:** Explicit authority boundaries for ecosystem participants

---

## AUTHORITY STRUCTURE

```
┌─────────────────────────────────────────────────────────┐
│         EXECUTIVE AUTHORITY                             │
│  (Governance Charter, Constitutional Amendments)        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌─────────┬──────────┬──────────────┐
    │SANSKAR  │ RAJYA    │ Enforcement  │
    │(Decision│(Validates│(Permits/     │
    │Making)  │Boundaries│Rejects)      │
    └────┬────┴─────┬────┴──────┬───────┘
         │          │           │
         │          │     ┌─────┴──────┐
         │          │     │            │
         ▼          ▼     ▼            ▼
      ┌──────────────────────────────────────┐
      │  Bucket (Persistence)                │
      │  InsightBridge (Observability)       │
      └──────────────────────────────────────┘
```

---

## AUTHORITY MATRIX

| Authority | Owns | Can Do | Cannot Do | Escalation |
|-----------|------|--------|-----------|-----------|
| **SANSKAR** | Ranking Logic | Generate scores 0-1 for items | Change governance rules, override RAJYA | Proposal to Executive |
| **RAJYA** | Governance Validation | Validate boundary compliance, reject violations | Modify boundaries, change constitution | Executive review + amendment |
| **Enforcement** | Apply/Reject Decision | Apply valid rankings, reject invalid ones | Change what is "valid", modify boundaries | Proposal to Executive |
| **Bucket** | Persistence | Store validated decisions, maintain replicas | Modify what to store, validate contracts | Enforcement team decision |
| **InsightBridge** | Observability | Emit telemetry, track correlation | Suppress failures, alter audit trail | Incident Commander review |

---

## PHASE-BY-PHASE AUTHORITY

### Phase 1: Signal Input
**Authority:** Signal Source  
**Decision:** Accept signal  
**Scope:** Input format validation only  
**Output:** Signal → SANSKAR

### Phase 2: SANSKAR Ranking
**Authority:** SANSKAR  
**Decision:** Calculate rankings (0-1 scores)  
**Scope:** Ranking algorithm implementation  
**Limits:** 
- Cannot reject based on governance
- Cannot modify confidence manually
- Cannot access external state

**Output:** Rankings + confidence_state → RAJYA

### Phase 3: RAJYA Governance Validation
**Authority:** RAJYA  
**Decision:** Validate governance boundaries  
**Scope:** Constitutional checks only  
**Enforces:** 4 boundaries
1. Confidence ≠ Legitimacy
2. Intelligence ≠ Governance
3. Observability ≠ Authority
4. Replay Stability ≠ Permission

**Limits:**
- Cannot modify SANSKAR rankings
- Cannot change decisions
- Can only ACCEPT/REJECT

**Output:** Validation result → Enforcement

### Phase 4: Enforcement Authority Decision
**Authority:** Enforcement  
**Decision:** APPLY or REJECT decision  
**Scope:** Apply valid decisions only  
**Limits:**
- Cannot override RAJYA validation
- Cannot permit invalid decisions
- Cannot change governance

**Output:** Apply/Reject → Bucket

### Phase 5: Bucket Persistence
**Authority:** Bucket  
**Decision:** Persist to truth store  
**Scope:** Storage implementation  
**Guarantees:**
- 3+ replicas across regions
- Immutable audit trail
- Durability SLA

**Limits:**
- Cannot modify persisted data
- Cannot selective retention
- Cannot filter events

**Output:** Persisted → InsightBridge

### Phase 6: InsightBridge Observability
**Authority:** InsightBridge  
**Decision:** Emit telemetry  
**Scope:** Observability only (read-only)  
**Emits:**
- Full transaction traces
- Latency metrics
- Governance checks
- Failure events

**Limits:**
- Cannot suppress failures
- Cannot filter audit trail
- Cannot modify events
- Cannot make decisions

**Output:** Telemetry → Monitoring

---

## DECISION MATRIX

### Who Decides What?

**Can SANSKAR decide?**
- ✓ Ranking scores for each item
- ✗ Whether ranking is valid
- ✗ Whether decision should be applied
- ✗ Whether governance is violated

**Can RAJYA decide?**
- ✓ Whether governance boundaries held
- ✓ Reject invalid decisions
- ✗ What the ranking scores should be
- ✗ Whether to force-apply despite violation

**Can Enforcement decide?**
- ✓ Apply valid decisions
- ✓ Reject invalid decisions
- ✗ What is "valid" (RAJYA decides)
- ✗ Override governance

**Can Bucket decide?**
- ✓ How/where to persist
- ✓ Replica strategy
- ✗ What to persist (Enforcement decides)
- ✗ Selective retention

**Can InsightBridge decide?**
- ✓ Which events to emit
- ✓ Telemetry sampling
- ✗ What happens to data
- ✗ Suppress any events

---

## ESCALATION PATHS

### Scenario 1: SANSKAR Output Seems Wrong
```
Developer
    ↓
Review SANSKAR Algorithm (Line Xs of core.py)
    ↓
Decision: Algorithm correct but needs tuning?
    ├─ YES → Tune parameters, redeploy (no escalation)
    └─ NO → Find root cause, propose fix
        ↓
    Fix approved? (Code review)
        ├─ YES → Deploy fix, test, monitor
        └─ NO → Architect review required
```

### Scenario 2: RAJYA Rejects Valid Decision
```
Operator
    ↓
Check governance violation reason
    ↓
Decision: Is boundary rule correct?
    ├─ YES → Fix SANSKAR output, retry (no escalation)
    └─ NO → Boundary rule is wrong
        ↓
    Proposal to amend boundary
        ├─ APPROVE → Executive review → Constitutional amendment
        └─ REJECT → Stand with current boundary
```

### Scenario 3: Enforcement Won't Apply Approved Decision
```
RAJYA
    ↓
Decision was validated (passed RAJYA check)
    ↓
Contact Enforcement team
    ↓
Check: Is Enforcement correctly checking RAJYA signal?
    ├─ BUG → Fix code, deploy
    └─ WORKING AS DESIGNED → Escalate if governance differs
```

### Scenario 4: Non-Deterministic Results
```
Operator (detected in replay)
    ↓
Identify phase with non-determinism
    ├─ SANSKAR → Review algorithm for random state
    ├─ RAJYA → Review governance checks
    ├─ Bucket → Review persistence logic
    └─ OTHER → Investigate storage/network
        ↓
    Fix root cause (remove randomness, fix seeds)
        ↓
    Test determinism: python test.py --test-determinism
        ↓
    Approve fix (code review)
        ↓
    Deploy + monitor
```

### Scenario 5: Governance Violation Detected
```
CRITICAL → HALT SYSTEM IMMEDIATELY

    ↓
Incident Commander convened
    ↓
Investigation phase
    ├─ Root cause: Code bug? → Fix + redeploy
    ├─ Root cause: Boundary wrong? → Executive review
    └─ Root cause: Orchestration error? → Process fix
        ↓
    Resolution approved?
        ├─ YES → Implement fix
        └─ NO → Escalate to Board
                ↓
            Accept governance violation?
                ├─ YES → Amend constitution (vote)
                └─ NO → Reject transaction type
```

---

## GOVERNANCE CHARTER

### Constitutional Boundaries (Immutable)

**Boundary 1: Confidence ≠ Legitimacy**
- High confidence scores do NOT make decision legitimate
- Low confidence scores do NOT invalidate decision
- Confidence state is decision metadata, not permission

**Boundary 2: Intelligence ≠ Governance**
- Smart algorithm does NOT bypass governance
- Complex calculation does NOT grant permissions
- Algorithm correctness is separate from governance validity

**Boundary 3: Observability ≠ Authority**
- Seeing event does NOT mean can control it
- Monitoring system does NOT make decisions
- Telemetry is read-only

**Boundary 4: Replay Stability ≠ Permission**
- Reproducible transaction does NOT mean repeatable
- Same input/output does NOT mean currently valid
- Determinism is property, not permission

### Amendments to Boundaries

**Process:**
1. Proposal to Executive (+ rationale)
2. Review by Governance Board (30 days)
3. Public notice of proposed change (7 days)
4. Constitutional amendment vote (supermajority)
5. Implementation in code
6. Full system regression test
7. Monitoring period (30 days)

**No shortcuts:** Governance boundaries cannot be bypassed or suspended.

---

## AUTHORITY SCOPE BY ROLE

### SANSKAR Developer
**Can:**
- Modify ranking algorithm
- Change confidence calculation
- Update signal processing logic
- Propose governance improvements

**Cannot:**
- Override RAJYA rejection
- Modify governance code
- Apply decisions directly

**Escalation:** To RAJYA governance architect

### RAJYA Developer
**Can:**
- Modify governance checks
- Add new boundary validations
- Implement rejection logic
- Audit governance violations

**Cannot:**
- Approve invalid decisions
- Modify SANSKAR rankings
- Override Enforcement

**Escalation:** To Executive Board

### Enforcement Developer
**Can:**
- Implement decision application logic
- Handle valid/invalid states
- Log enforcement decisions
- Optimize application flow

**Cannot:**
- Decide what is "valid" (RAJYA does)
- Override governance
- Persist decisions (Bucket does)

**Escalation:** To RAJYA team

### Bucket Developer
**Can:**
- Optimize storage layer
- Manage replication
- Implement durability features
- Monitor persistence

**Cannot:**
- Modify what to persist (Enforcement decides)
- Suppress events
- Alter audit trail

**Escalation:** To Operations

### InsightBridge Developer
**Can:**
- Implement telemetry collection
- Optimize observability
- Manage trace correlation
- Implement sampling

**Cannot:**
- Suppress failures
- Alter event data
- Make decisions based on events

**Escalation:** To Incident Commander

### Operator
**Can:**
- Start/stop system
- Monitor health
- Handle timeouts
- Restart services

**Cannot:**
- Modify governance
- Override decisions
- Suppress failures

**Escalation:** To SRE team

### Incident Commander
**Can:**
- Declare incidents
- Coordinate response
- Authorize emergency procedures
- Escalate to Executive

**Cannot:**
- Override governance
- Modify code
- Suppress audit trail

**Escalation:** To Executive Board

---

## DECISION FLOW CHART

```
New Transaction Input
    │
    ▼
SANSKAR: Generate Rankings
    │ (Always succeeds if input valid)
    ▼
RAJYA: Validate Boundaries
    │
    ├─ PASS ─→ Enforcement: Apply Decision
    │            │ (Always succeeds for valid)
    │            ▼
    │         Bucket: Persist
    │            │ (Always succeeds)
    │            ▼
    │         InsightBridge: Emit Telemetry
    │            │ (Always succeeds)
    │            ▼
    │         Output to Requester: SUCCESS
    │
    └─ FAIL ─→ Enforcement: Reject Decision
                 │ (Always rejects invalid)
                 ▼
              Return Error: GOVERNANCE_VIOLATION
              (No persistence, no application)
```

---

## AUTHORITY ESCALATION HIERARCHY

```
Level 4 (Constitutional): Executive Board
  - Can amend governance charter
  - Can change boundaries
  - Can change architecture
  - Monthly meetings

Level 3 (Governance): Incident Commander
  - Can investigate violations
  - Can order emergency procedures
  - Can halt system
  - 24/7 on-call

Level 2 (Operations): SRE Team
  - Can restart services
  - Can handle failures
  - Can debug issues
  - Daily coordination

Level 1 (Development): Developers
  - Can modify code
  - Can deploy changes
  - Can optimize
  - Continuous

Authority increases as you go up.
Responsibility increases as you go down.
```

---

## SUMMARY TABLE

| Participant | Role | Authority Level | Makes Decisions | Cannot Override |
|-------------|------|-----------------|-----------------|-----------------|
| SANSKAR | Algorithm | 1 (Development) | Ranking scores | Boundaries |
| RAJYA | Validator | 1 (Development) | Boundary compliance | Decisions |
| Enforcement | Authority | 1 (Development) | Apply/Reject | Boundaries |
| Bucket | Storage | 1 (Development) | Persistence | Content |
| InsightBridge | Observability | 1 (Development) | Telemetry | Data suppression |
| Operator | Operations | 2 (Operations) | System health | Decisions |
| Incident Cmdr | Leadership | 3 (Governance) | Crisis response | Boundaries |
| Executive Board | Governance | 4 (Constitutional) | Charter amendments | Principles |

---

## CONFLICT RESOLUTION

If two authorities disagree:

**Level 1 vs Level 1:** Code review + consensus (48 hours)  
**Level 1 vs Level 2:** SRE decides (4 hours)  
**Level 2 vs Level 3:** Incident Commander decides (2 hours)  
**Level 3 vs Level 4:** Executive Board votes (30 days)  

**In case of tie:** Status quo (no change)

---

## CONCLUSION

**Key Principle:** No single entity has absolute authority.

**System Design:** Authority is distributed across layers:
- **Layer 1:** Implementation (developers)
- **Layer 2:** Operations (SRE)
- **Layer 3:** Governance (incident management)
- **Layer 4:** Constitution (executive board)

**Result:** Decisions are checked at multiple levels. Mistakes are caught before causing harm.

---

**Version:** Phase 11 (May 28, 2026)  
**Status:** Ready for Governance Review
