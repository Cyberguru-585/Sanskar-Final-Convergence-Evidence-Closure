# AUTHORITY_MATRIX.md — Phase 4: Governance & Boundary Enforcement



---

## 1. AUTHORITY MATRIX (CANONICAL)

### System Authorities

| Authority | SANSKAR | RAJYA | ENFORCEMENT | Bucket | InsightBridge |
|-----------|---------|-------|-------------|--------|---------------|
| **Intelligence** | ✓ OWN | ✓ read | ✓ read | ✓ store | ✓ metric |
| **Governance** | ✗ NOT | ✓ OWN | ✗ execute only | ✗ NOT | ✗ NOT |
| **Enforcement** | ✗ NOT | ✗ NOT | ✓ OWN | ✗ NOT | ✗ NOT |
| **Truth/Events** | ✗ NOT | ✗ NOT | ✗ NOT | ✓ OWN | ✗ NOT |
| **Observability** | ✗ NOT | ✗ NOT | ✗ NOT | ✗ NOT | ✓ OWN |

### Detailed Authority Breakdown

#### SANSKAR Authority

**CAN:**
- ✓ Compute entity rankings
- ✓ Produce confidence scores
- ✓ Emit decision_state metadata
- ✓ Propose to RAJYA
- ✓ Declare uncertainty
- ✓ Participate in replay
- ✓ Read RAJYA decisions (replay only)
- ✓ Query Bucket via trace_id (replay only)
- ✓ Query InsightBridge metrics (read-only)

**CANNOT:**
- ✗ Govern (RAJYA governs)
- ✗ Enforce (ENFORCEMENT enforces)
- ✗ Write truth directly (Bucket writes)
- ✗ Emit telemetry directly (InsightBridge emits)
- ✗ Mutate RAJYA decisions
- ✗ Bypass ENFORCEMENT
- ✗ Configure other systems
- ✗ Access hidden state of other systems

**Ceiling:** Intelligence derivation layer only

---

#### RAJYA Authority

**CAN:**
- ✓ Receive SANSKAR recommendations
- ✓ Approve/reject/defer decisions
- ✓ Override SANSKAR recommendations
- ✓ Enforce governance rules
- ✓ Sign decisions with authority
- ✓ Delegate to ENFORCEMENT

**CANNOT:**
- ✗ Compute intelligence (SANSKAR computes)
- ✗ Enforce boundaries (ENFORCEMENT enforces)
- ✗ Write truth directly (must use Bucket)
- ✗ Emit telemetry directly (must use InsightBridge)
- ✗ Mutate enforcement directives (read-only after handoff)

**Ceiling:** Governance decision authority only

---

#### ENFORCEMENT Authority

**CAN:**
- ✓ Receive RAJYA governance decisions
- ✓ Enforce boundaries
- ✓ Block unauthorized operations
- ✓ Fail-closed on uncertainty
- ✓ Generate enforcement directives
- ✓ Report violations

**CANNOT:**
- ✗ Compute intelligence (SANSKAR computes)
- ✗ Make governance decisions (RAJYA decides)
- ✗ Write truth directly (Bucket writes)
- ✗ Emit telemetry directly (InsightBridge emits)
- ✗ Override RAJYA decisions

**Ceiling:** Fail-closed boundary enforcement only

---

#### Bucket Authority

**CAN:**
- ✓ Receive and store all events
- ✓ Ensure immutability
- ✓ Support replay from trace_id
- ✓ Serve as truth source
- ✓ Emit events to InsightBridge
- ✓ Verify event signatures

**CANNOT:**
- ✗ Compute intelligence
- ✗ Make governance decisions
- ✗ Enforce boundaries
- ✗ Emit telemetry directly
- ✗ Mutate stored events
- ✗ Override event ownership

**Ceiling:** Event store/truth authority only

---

#### InsightBridge Authority

**CAN:**
- ✓ Receive events from Bucket
- ✓ Emit observability signals
- ✓ Provide metrics queries
- ✓ Store telemetry history
- ✓ Support dashboards/alerts

**CANNOT:**
- ✗ Compute intelligence
- ✗ Make governance decisions
- ✗ Enforce boundaries
- ✗ Write truth events (read-only from Bucket)
- ✗ Mutate event data

**Ceiling:** Observability/metrics authority only

---

## 2. BOUNDARY CHECKS

### Boundary 1: SANSKAR → RAJYA

**What flows across:** Intelligence output (rankings, confidence)  
**What blocks:** Governance decisions, enforcement directives, truth writes  

```python
def check_sanskar_to_rajya_boundary(sanskar_output: Dict) -> Tuple[bool, str]:
    """
    Verify SANSKAR output respects boundary.
    
    Returns: (allowed, reason)
    """
    
    # Forbidden fields
    forbidden = {
        "governance_decision",
        "enforcement_directive", 
        "bucket_write_direct",
        "authority_override",
        "observability_signal"
    }
    
    found_forbidden = forbidden & set(sanskar_output.keys())
    if found_forbidden:
        return False, f"SANSKAR output contains forbidden fields: {found_forbidden}"
    
    
    required = {"trace_id", "stage", "entities", "ranking", "metadata"}
    missing = required - set(sanskar_output.keys())
    if missing:
        return False, f"SANSKAR output missing required fields: {missing}"
    
    
    if sanskar_output.get("stage") != "sanskar":
        return False, f"Stage is '{sanskar_output.get('stage')}', not 'sanskar'"
    
    
    owner = sanskar_output.get("metadata", {}).get("owner")
    if owner != "sanskar":
        return False, f"Owner is '{owner}', not 'sanskar'"
    
    return True, "PASS"
```

### Boundary 2: RAJYA → ENFORCEMENT

**What flows across:** Governance decisions (approve/reject/defer)  
**What blocks:** Intelligence rankings, observability signals  

```python
def check_rajya_to_enforcement_boundary(rajya_decision: Dict) -> Tuple[bool, str]:
    """
    Verify RAJYA decision respects boundary.
    """
    
    
    auth = rajya_decision.get("authority_check", {})
    if auth.get("decision_maker") != "rajya":
        return False, "Decision does not come from RAJYA"
    if auth.get("constitutional_authority") is not True:
        return False, "RAJYA authority check failed"
    
    valid_decisions = {"APPROVED", "REJECTED", "DEFERRED"}
    if rajya_decision.get("decision") not in valid_decisions:
        return False, f"Invalid decision: {rajya_decision.get('decision')}"
    
   
    forbidden_keywords = {"ranking", "score", "confidence", "algorithm"}
    for key in forbidden_keywords:
        if key in rajya_decision:
            return False, f"RAJYA decision contains forbidden field: {key}"
    
    return True, "PASS"
```

### Boundary 3: ENFORCEMENT → Execution

**What flows across:** Enforcement directives (action, target, urgency)  
**What blocks:** Governance overrides, observability signals  

### Boundary 4: Execution → Bucket

**What flows across:** Event records (outcome, resources, timing)  
**What blocks:** Mutable data, unowned events  

```python
def check_execution_to_bucket_boundary(event_record: Dict) -> Tuple[bool, str]:
    
    ownership = event_record.get("ownership", {})
    if ownership.get("owner") != "bucket":
        return False, f"Event owner is '{ownership.get('owner')}', not 'bucket'"
    if ownership.get("immutable") is not True:
        return False, "Event must be marked immutable"
    
    
    forbidden = {"ranking", "confidence", "governance_decision"}
    found = forbidden & set(event_record.keys())
    if found:
        return False, f"Event contains forbidden fields: {found}"
    
    return True, "PASS"
```

### Boundary 5: Bucket → InsightBridge

**What flows across:** Metrics/telemetry derived from events  
**What blocks:** Raw event data modifications  

---

## 3. DRIFT DETECTION

### Drift Type 1: Intelligence→Authority Drift

**Definition:** SANSKAR produces governance decisions or enforcement directives.

```python
def detect_intelligence_to_authority_drift(sanskar_output: Dict) -> Tuple[bool, str]:
   
    drift_indicators = {
        "governance_decision": "SANSKAR producing governance decision",
        "enforcement_directive": "SANSKAR producing enforcement directive",
        "decision_maker": "SANSKAR claiming decision authority",
        "bucket_immutable_mark": "SANSKAR claiming immutability (Bucket-only authority)"
    }
    
    detected_drift = []
    for indicator, description in drift_indicators.items():
        if indicator in sanskar_output:
            detected_drift.append(description)
    
    if detected_drift:
        return True, f"Intelligence→Authority drift detected: {detected_drift}"
    
    return False, "No drift detected"
```

### Drift Type 2: Observability→Authority Drift

**Definition:** InsightBridge produces governance decisions or mutates events.

```python
def detect_observability_to_authority_drift(insightbridge_output: Dict) -> Tuple[bool, str]:
    
    
    drift_indicators = {
        "event_mutation": "InsightBridge mutating event data",
        "governance_decision": "InsightBridge producing governance decision",
        "decision_maker": "InsightBridge claiming decision authority"
    }
    
    detected_drift = []
    for indicator, description in drift_indicators.items():
        if indicator in insightbridge_output:
            detected_drift.append(description)
    
    if detected_drift:
        return True, f"Observability→Authority drift detected: {detected_drift}"
    
    return False, "No drift detected"
```

### Drift Type 3: Testing→Governance Drift

**Definition:** Test/validation system produces governance decisions affecting production.

```python
def detect_testing_to_governance_drift(test_output: Dict, is_production_env: bool) -> Tuple[bool, str]:
    
    
    if not is_production_env:
        return False, "Not production environment — testing allowed"
    
    # In production, test outputs must not affect governance
    if test_output.get("impacts_governance") == True:
        return True, "Testing→Governance drift in production: test output affects governance"
    
    return False, "No testing→governance drift"
```

### Drift Type 4: Replay→Truth Authority Drift

**Definition:** Replay system mutates truth records instead of read-only verification.

```python
def detect_replay_to_truth_drift(replay_operation: Dict) -> Tuple[bool, str]:
    
    
    if replay_operation.get("operation") == "write":
        return True, "Replay→Truth drift: replay attempting write operation"
    
    if replay_operation.get("mutates_event") == True:
        return True, "Replay→Truth drift: replay mutating event data"
    
    return False, "Replay is read-only"
```

---

## 4. HIDDEN AUTHORITY CHECKS

### Check 1: Undeclared Authority

**Definition:** System exerts authority not declared in its contracts.

```python
def check_undeclared_authority(system_output: Dict, system_name: str) -> List[str]:
   
    
    violations = []
    
   
    expected_authority = {
        "sanskar": {"intelligence_ranking", "confidence_score", "decision_state"},
        "rajya": {"governance_decision", "authority_check"},
        "enforcement": {"enforcement_directive", "boundary_check"},
        "bucket": {"event_write", "immutability_guarantee"},
        "insightbridge": {"metric_emission", "telemetry_query"}
    }
    
    
    actual_operations = set(system_output.keys())
    allowed_operations = expected_authority.get(system_name, set())
    
    undeclared = actual_operations - allowed_operations
    for op in undeclared:
        # Some keys are metadata, not authority operations
        if op not in {"trace_id", "stage", "timestamp", "metadata", "contract_version"}:
            violations.append(f"Undeclared operation: {op}")
    
    return violations
```

### Check 2: Cross-Boundary Authority

**Definition:** System exerts authority across unauthorized boundaries.

```python
def check_cross_boundary_authority(from_system: str, to_system: str, 
                                   operation: str) -> Tuple[bool, str]:
    
    
    
    allowed_transitions = {
        ("sanskar", "rajya"): {"intelligence_output"},
        ("rajya", "enforcement"): {"governance_decision"},
        ("enforcement", "execution"): {"enforcement_directive"},
        ("execution", "bucket"): {"event_record"},
        ("bucket", "insightbridge"): {"telemetry_emission"}
    }
    
    key = (from_system, to_system)
    if key not in allowed_transitions:
        return False, f"No authorized transition from {from_system} to {to_system}"
    
    allowed_ops = allowed_transitions[key]
    if operation not in allowed_ops:
        return False, f"Operation '{operation}' not allowed in {key} transition"
    
    return True, "Transition allowed"
```

### Check 3: Authority Ceiling Violation

**Definition:** System attempts operations above its ceiling.

```python
def check_authority_ceiling(system_name: str, attempted_operation: str) -> Tuple[bool, str]:
    
    ceilings = {
        "sanskar": "intelligence_derivation",  # Cannot exceed this
        "rajya": "governance_decision",
        "enforcement": "fail_closed_enforcement",
        "bucket": "event_storage",
        "insightbridge": "observability"
    }
    
    ceiling = ceilings.get(system_name)
    
    # Define what violates each ceiling
    ceiling_violations = {
        "sanskar": {
            "governance_decision",
            "enforcement_directive",
            "bucket_write",
            "observability_emit",
            "system_configuration"
        },
        "rajya": {
            "intelligence_computation",
            "enforcement_execution",
            "bucket_write",
            "observability_emit"
        },
        # ... more definitions
    }
    
    violations = ceiling_violations.get(system_name, set())
    
    if attempted_operation in violations:
        return False, f"Operation '{attempted_operation}' violates {system_name}'s authority ceiling ({ceiling})"
    
    return True, "Within authority ceiling"
```

---

## 5. NEGATIVE AUTHORITY DECLARATION

### What SANSKAR is Explicitly NOT

```json
{
  "system": "sanskar",
  "what_it_is": "bounded_intelligence_producer",
  "what_it_is_NOT": [
    "NOT a governance authority",
    "NOT an enforcement authority",
    "NOT a truth authority",
    "NOT an observability authority",
    "NOT a configuration authority",
    "NOT a security authority",
    "NOT an access control authority",
    "NOT a policy enforcement system",
    "NOT a system integrator",
    "NOT an operator (humans decide final actions)"
  ]
}
```

### What RAJYA is Explicitly NOT

```json
{
  "system": "rajya",
  "what_it_is": "governance_authority",
  "what_it_is_NOT": [
    "NOT an intelligence producer",
    "NOT an enforcement executor",
    "NOT a truth authority",
    "NOT an observability authority",
    "NOT a resource allocator (delegates to ENFORCEMENT)"
  ]
}
```

### What ENFORCEMENT is Explicitly NOT

```json
{
  "system": "enforcement",
  "what_it_is": "boundary_enforcer_fail_closed",
  "what_it_is_NOT": [
    "NOT a governance authority",
    "NOT an intelligence producer",
    "NOT a truth authority",
    "NOT an observability authority",
    "NOT a decision maker (only executes decisions)"
  ]
}
```

### What Bucket is Explicitly NOT

```json
{
  "system": "bucket",
  "what_it_is": "event_store_truth_authority",
  "what_it_is_NOT": [
    "NOT a governance authority",
    "NOT an intelligence producer",
    "NOT an enforcement authority",
    "NOT an observability authority",
    "NOT a mutator of events (immutable)",
    "NOT a business logic engine"
  ]
}
```

### What InsightBridge is Explicitly NOT

```json
{
  "system": "insightbridge",
  "what_it_is": "observability_telemetry_authority",
  "what_it_is_NOT": [
    "NOT a governance authority",
    "NOT an intelligence producer",
    "NOT an enforcement authority",
    "NOT a truth authority (read-only from Bucket)",
    "NOT a decision maker",
    "NOT an alerting system (independent of observability)"
  ]
}
```

---

## 6. RUNTIME ENFORCEMENT

### Authority Detector

The Authority Detector monitors all system outputs and blocks violations.

```python
class AuthorityDetector:
    
    def validate_output(self, stage_name: str, output: Dict) -> Tuple[bool, List[str]]:
        
        violations = []
        
        
        undeclared = check_undeclared_authority(output, stage_name)
        violations.extend(undeclared)
        
       
        if stage_name == "sanskar":
            drifted, reason = detect_intelligence_to_authority_drift(output)
            if drifted:
                violations.append(reason)
        
       
        for key in output.keys():
            within_ceiling, reason = check_authority_ceiling(stage_name, key)
            if not within_ceiling:
                violations.append(reason)
        
        
        next_stage = self.get_next_stage(stage_name)
        if next_stage:
            allowed, reason = self.check_boundary(stage_name, next_stage, output)
            if not allowed:
                violations.append(reason)
        
        return len(violations) == 0, violations
    
    def block_or_warn(self, violations: List[str], is_critical: bool) -> None:
        
        if is_critical and violations:
            raise AuthorityViolation(f"Critical violations: {violations}")
        elif violations:
            logger.warning(f"Authority violations (non-critical): {violations}")
```

---

## 7. GOVERNANCE AUDIT REPORT

Example output from continuous monitoring:

```json
{
  "audit_timestamp": "2026-06-03T12:00:00Z",
  "audit_duration_hours": 1,
  "total_requests_processed": 2847,
  "authority_violations_detected": 3,
  "violations": [
    {
      "request_id": "trace-7af92100",
      "violating_system": "sanskar",
      "violation_type": "undeclared_authority",
      "detail": "SANSKAR output contained 'governance_decision' field",
      "severity": "CRITICAL",
      "action_taken": "BLOCKED"
    },
    {
      "request_id": "trace-7af92101",
      "violating_system": "insightbridge",
      "violation_type": "observability_to_authority_drift",
      "detail": "InsightBridge attempted to mutate event record",
      "severity": "CRITICAL",
      "action_taken": "BLOCKED"
    },
    {
      "request_id": "trace-7af92102",
      "violating_system": "enforcement",
      "violation_type": "ceiling_violation",
      "detail": "ENFORCEMENT attempted to emit governance decision",
      "severity": "CRITICAL",
      "action_taken": "BLOCKED"
    }
  ],
  "boundary_integrity": {
    "sanskar_to_rajya": "100% compliant",
    "rajya_to_enforcement": "100% compliant",
    "enforcement_to_execution": "100% compliant",
    "execution_to_bucket": "100% compliant",
    "bucket_to_insightbridge": "100% compliant"
  },
  "drift_status": {
    "intelligence_to_authority": "NO DRIFT",
    "observability_to_authority": "NO DRIFT",
    "testing_to_governance": "NO DRIFT",
    "replay_to_truth": "NO DRIFT"
  },
  "recommendation": "All systems operating within authority boundaries. No governance risks detected."
}
```

---

## NEXT PHASE

**Phase 5 — Deployment/Testing:** Create 5-10 minute deterministic self-test including healthy path, invalid input, dependency unavailable, trace break, and authority violation scenarios.

