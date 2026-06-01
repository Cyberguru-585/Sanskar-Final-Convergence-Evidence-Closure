# authority_boundary_map.md

# CANONICAL AUTHORITY BOUNDARY MAP

**Date:** June 1, 2026  
**Status:** VERIFIED at runtime (Phase 4)  
**Drift Status:** NO DRIFT DETECTED  
**Last Audit:** Governance Runtime Audit, Phase 4

---

## EXECUTIVE SUMMARY

This document establishes the **canonical definition** of all service authorities and responsibilities within the SANSKAR ecosystem. This map is:

1. **Immutable** - Does not change without formal review
2. **Runtime-enforced** - Violations are detected and blocked
3. **Architecturally sound** - Intelligence ≠ Governance (clear separation)
4. **Drift-monitored** - Continuous verification against declarations

---

## CANONICAL DEFINITIONS

### SERVICE: SANSKAR
**Official Identity:** `Bounded Intelligence Producer`  
**NOT:** Decision-making authority  
**NOT:** Governance authority

#### What SANSKAR CAN Do
- Generate rankings based on input data
- Calculate confidence scores
- Produce adaptive intelligence signals
- Generate explanations (comparative analysis)
- Participate in deterministic replay

#### What SANSKAR CANNOT Do
- Make governance decisions 
- Change policy 
- Override RAJYA authority 
- Modify trace_id 
- Make fail-closed decisions 

#### Authority Scope
**ZERO governance authority.** SANSKAR is purely an **intelligence layer**. All intelligence must be validated by RAJYA before acting.

#### Proof
- Authority violation detector (Phase 4): SANSKAR blocking test BLOCKED governance attempt
- Governance audit contract: SANSKAR explicitly in `cannot_do: ["governance_decisions"]`

---

### SERVICE: RAJYA
**Official Identity:** `Governance Authority`  
**Scope:** FULL governance authority over all decisions  
**Authority Level:** SUPREME

#### What RAJYA CAN Do
- Validate governance policies
- Make binding governance decisions
- Enforce constitutional boundaries
- Override SANSKAR recommendations
- Set fail-closed defaults
- Approve decision execution

#### What RAJYA CANNOT Do
- Generate rankings  (that's SANSKAR's job)
- Modify confidence scores directly 
- Bypass enforcement 
- Mutate immutable fields 

#### Authority Scope
**FULL governance scope.** RAJYA is the **exclusive authority** for all governance decisions. No other service can override RAJYA.

#### Proof
- Authority violation detector (Phase 4): RAJYA blocking test BLOCKED ranking attempt
- Governance audit contract: RAJYA in `can_do: ["governance_validation", "boundary_enforcement"]`

---

### SERVICE: ENFORCEMENT
**Official Identity:** `Boundary Enforcer`  
**Scope:** Enforce boundaries, NOT make policy

#### What ENFORCEMENT CAN Do
- Validate authority boundaries
- Check cross-service contracts
- Activate fail-closed behavior
- Verify trace immutability
- Block boundary violations

#### What ENFORCEMENT CANNOT Do
- Make governance decisions 
- Change policy 
- Modify SANSKAR output 
- Override RAJYA 

#### Authority Scope
**Fail-closed enforcement only.** ENFORCEMENT is a **validator**, not a decision-maker. It defaults to DENY unless explicitly authorized by RAJYA.

#### Proof
- Deployment validated: ENFORCEMENT service boundary enforcer identity confirmed
- Governance audit: ENFORCEMENT in `can_do: ["boundary_enforcement"]`

---

## BOUNDARY CROSSING RULES

### SANSKAR → RAJYA Boundary
**Type:** Intelligence → Governance  
**Rule:** SANSKAR produces ranking, RAJYA validates governance  
**Contract Version:** v1  
**Trace Propagation:** ✓ Immutable  
**Proof:** Cross-ecosystem execution proof (Phase 2)

```
Input: SANSKAR ranking
Output: RAJYA governance_status (APPROVED/REJECTED)
```

### RAJYA → Bucket Boundary
**Type:** Governance → Persistence  
**Rule:** RAJYA-approved decisions are persisted  
**Contract Version:** v1  
**Trace Propagation:** ✓ Immutable  
**Proof:** Cross-ecosystem execution proof (Phase 2)

```
Input: RAJYA decision
Output: Bucket persistence_status (PERSISTED)
```

### Bucket → InsightBridge Boundary
**Type:** Persistence → Observability  
**Rule:** Decisions in store emit telemetry  
**Contract Version:** v1  
**Trace Propagation:** ✓ Immutable  
**Proof:** Cross-ecosystem execution proof (Phase 2)

```
Input: Bucket record
Output: InsightBridge telemetry_status (COLLECTED)
```

---

## DRIFT DETECTION

### What is Drift?
Drift = difference between declared authority and actual behavior

### Current Drift Status:  NO DRIFT

| Service | Declared | Actual | Drift | Status |
|---------|----------|--------|-------|--------|
| SANSKAR | Intelligence producer | Intelligence producer |  Match | OK |
| RAJYA | Governance authority | Governance authority |  Match | OK |
| ENFORCEMENT | Boundary enforcer | Boundary enforcer |  Match | OK |

### Drift Monitoring
- Continuous at runtime (Phase 4)
- Any drift triggers [DRIFT] alert
- Drift = immediate incident

---

## GOVERNANCE VIOLATIONS (DETECTED & BLOCKED)

During Phase 4 Governance Audit, the system detected these attempts:

### Violation 1: SANSKAR Attempted Governance
```
Event: SANSKAR tried action "governance_decisions"
Status: BLOCKED ✓
Reason: Outside SANSKAR authority
```

### Violation 2: RAJYA Attempted Ranking
```
Event: RAJYA tried action "ranking"
Status: BLOCKED ✓
Reason: Outside RAJYA authority (SANSKAR's job)
```

### Violation 3: Trace Mutation Attempt
```
Event: trace-audit-002 was mutated
Status: CAUGHT ✓
Reason: Trace immutability enforced
```

---

## CRITICAL INVARIANTS

These must NEVER be violated:

### Invariant 1: SANSKAR = Not Decision Authority
```
∀ time t: SANSKAR.authority == NONE
Cannot be changed without full re-architecture
```

### Invariant 2: RAJYA = Exclusive Governance Authority
```
∀ decision d: d.authority_source == RAJYA
No other service can make governance decisions
```

### Invariant 3: Trace ID Immutability
```
∀ trace_id t, service s: trace_id(t, s) == original(t)
Mutations are violations
```

### Invariant 4: Fail-Closed Default
```
∀ boundary b: if uncertain(b) then action = DENY
No exceptions
```

---

## CROSS-REFERENCE

| Document | Purpose | Authority Reference |
|----------|---------|---------------------|
| SELF_TESTING_PACKET.md | Deterministic validation | Tests authority boundaries |
| governance_runtime_report.json | Runtime audit results | Phase 4 proof |
| governance_audit_contract.json | Canonical contract | Defines all identities |
| operator_manual.md | Operational guidance | References this map |

---

## VERIFICATION CHECKLIST

Before deployment to production, verify:

- [ ] SANSKAR authority = NONE (not decision-making)
- [ ] RAJYA authority = FULL (exclusive governance)
- [ ] ENFORCEMENT = Fail-closed enforcer only
- [ ] No trace mutations detected
- [ ] No drift detected
- [ ] All boundary crossings preserve trace_id
- [ ] Authority violations are blocked at runtime
- [ ] Phase 4 Governance Audit passed
- [ ] No security drift in past 24 hours

---

## AMENDMENT PROCESS

To change this boundary map:

1. **Document** the proposed change
2. **Justify** why the change is necessary
3. **Risk assess** potential violations
4. **Implement** in code (update authority_map in governance_runtime_monitor.py)
5. **Test** new boundaries in Phase 4 audit
6. **Verify** no drift or violations
7. **Approve** by security and architecture teams
8. **Update** this document with amendment date

---

## CANONICAL FINALITY

This boundary map is the **source of truth** for all SANSKAR governance architecture.

- It is **verified at runtime** (Phase 4)
- It is **enforced by code** (governance_runtime_monitor.py)
- It is **tested deterministically** (SELF_TESTING_PACKET.md)
- It cannot be overridden by documentation

**Date Canonicalized:** June 1, 2026  
**Status:** FINAL  
**Amendment History:** None

---
