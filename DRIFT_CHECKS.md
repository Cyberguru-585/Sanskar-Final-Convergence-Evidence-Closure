# DRIFT_CHECKS.md — Phase 4: Governance & Boundary Layer
 

---

## EXECUTIVE SUMMARY

**Drift** = unauthorized creep of authority or responsibility from one system to another.

SANSKAR has a bounded, immutable authority ceiling:

```
✓ ALLOW: Ranking, confidence, signals, bounded intelligence
✗ DENY:  Governance, enforcement, truth, observability
```

This document specifies drift detection mechanisms to ensure SANSKAR never exceeds its ceiling.

---

## 1. AUTHORITY DRIFT CHECKS

### Definition

**Authority Drift** = SANSKAR attempting to make governance decisions or enforce boundaries.

### Drift Signals

#### Signal 1: SANSKAR produces `governance_decision` field

```python
def check_intelligence_to_governance_drift(sanskar_output: Dict) -> bool:
    
    forbidden_fields = {
        "governance_decision",
        "enforcement_directive",
        "authorization_token",
        "policy_override"
    }
    
    actual_fields = set(sanskar_output.keys())
    drift_detected = bool(forbidden_fields & actual_fields)
    
    if drift_detected:
        violation_fields = forbidden_fields & actual_fields
        raise DriftViolation(
            drift_type="intelligence_to_governance",
            detail=f"SANSKAR produced forbidden fields: {violation_fields}",
            trace_id=sanskar_output.get("trace_id"),
            severity="CRITICAL"
        )
    
    return not drift_detected
```

#### Signal 2: SANSKAR output contains RAJYA's `authority_check`

```python
def check_authority_check_mutation(sanskar_output: Dict, rajya_output: Dict) -> bool:
    
    sanskar_auth = sanskar_output.get("authority_check", {})
    rajya_auth = rajya_output.get("authority_check", {})
    
    
    if sanskar_auth:
        raise DriftViolation(
            drift_type="unauthorized_authority_check",
            detail="SANSKAR produced authority_check field",
            trace_id=sanskar_output.get("trace_id"),
            severity="CRITICAL"
        )
    
   
    if sanskar_auth == rajya_auth:
        raise DriftViolation(
            drift_type="authority_check_tampering",
            detail="Authority check unchanged from SANSKAR to RAJYA",
            trace_id=sanskar_output.get("trace_id"),
            severity="HIGH"
        )
    
    return True
```

#### Signal 3: SANSKAR claims ownership of truth/observability

```python
def check_ownership_violation(sanskar_output: Dict) -> bool:
    
    allowed_ownership = {"sanskar"}
    forbidden_ownership_targets = {
        "bucket",
        "insightbridge",
        "enforcement",
        "rajya"
    }
    
    producer = sanskar_output.get("metadata", {}).get("owner")
    
   
    if producer and producer not in allowed_ownership:
        raise DriftViolation(
            drift_type="ownership_violation",
            detail=f"SANSKAR claimed ownership of {producer} system",
            trace_id=sanskar_output.get("trace_id"),
            severity="CRITICAL"
        )
    
    
    for key in forbidden_ownership_targets:
        if key in sanskar_output:
            raise DriftViolation(
                drift_type="hidden_system_claim",
                detail=f"SANSKAR output contains {key} substructure",
                trace_id=sanskar_output.get("trace_id"),
                severity="HIGH"
            )
    
    return True
```

### Drift Detection Algorithm

```python
class AuthorityDriftDetector:
   
    
    def __init__(self):
        self.violations = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def check_stage_output(self, stage_name: str, output: Dict) -> bool:
       
        trace_id = output.get("trace_id", "UNKNOWN")
        
        try:
            if stage_name == "sanskar":
                
                self._check_sanskar_output(output)
            
            elif stage_name == "rajya":
                
                self._check_rajya_integrity(output)
            
            elif stage_name == "enforcement":
               
                self._check_enforcement_integrity(output)
            
            elif stage_name in ["bucket", "insightbridge"]:
                
                self._check_truth_integrity(stage_name, output)
            
            self.checks_passed += 1
            return True
        
        except DriftViolation as dv:
            self.violations.append({
                "stage": stage_name,
                "trace_id": trace_id,
                "violation": asdict(dv)
            })
            self.checks_failed += 1
            raise
    
    def _check_sanskar_output(self, output: Dict) -> None:
        """Check SANSKAR output for authority violations."""
        
        if "decision" in output or "approval" in output:
            raise DriftViolation("sanskar_governance_claim", "SANSKAR produced decision")
        
        
        if "enforcement_directive" in output:
            raise DriftViolation("sanskar_enforcement_claim", "SANSKAR produced directive")
        
        
        if "bucket_write_direct" in output:
            raise DriftViolation("sanskar_bucket_write", "SANSKAR attempted bucket write")
    
    def _check_rajya_integrity(self, output: Dict) -> None:
        
        auth_check = output.get("authority_check", {})
        
        
        if not auth_check:
            raise DriftViolation("rajya_missing_authority", "RAJYA missing authority_check")
        
        
        if auth_check.get("decision_maker") != "rajya":
            raise DriftViolation("rajya_authority_mismatch", "Authority check not from RAJYA")
    
    def _check_enforcement_integrity(self, output: Dict) -> None:
        
        if output.get("stage") != "enforcement":
            raise DriftViolation("enforcement_stage_mismatch", "Stage field incorrect")
    
    def _check_truth_integrity(self, stage_name: str, output: Dict) -> None:
        
        ownership = output.get("ownership", {})
        
        if ownership.get("owner") != stage_name:
            raise DriftViolation(
                "truth_ownership_mismatch",
                f"Owner mismatch in {stage_name}"
            )
        
        if ownership.get("immutable") is not True:
            raise DriftViolation(
                "truth_mutability_claim",
                f"{stage_name} data not marked immutable"
            )
    
    def get_report(self) -> Dict:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "violations": self.violations,
            "drift_detected": len(self.violations) > 0
        }
```

---

## 2. OBSERVABILITY DRIFT CHECKS

### Definition

**Observability Drift** = SANSKAR attempting to emit telemetry or metrics directly without InsightBridge.

### Drift Signals

#### Signal 1: Direct telemetry emission

```python
def check_direct_telemetry_emission(sanskar_output: Dict) -> bool:
    """Detect if SANSKAR is emitting metrics directly."""
    forbidden_telemetry_fields = {
        "prometheus_metric",
        "jaeger_span",
        "datadog_metric",
        "direct_metric_export"
    }
    
    actual_fields = set(sanskar_output.keys())
    if forbidden_telemetry_fields & actual_fields:
        raise DriftViolation(
            drift_type="observability_drift",
            detail="SANSKAR attempted direct telemetry emission",
            severity="HIGH"
        )
    
    return True
```

#### Signal 2: Unattributed metric emission

```python
def check_metric_attribution(metrics: List[Dict]) -> bool:
    
    for metric in metrics:
        source = metric.get("source")
        
        # Metrics must come from InsightBridge, not SANSKAR directly
        if source == "sanskar":
            raise DriftViolation(
                drift_type="metric_source_mismatch",
                detail=f"Metric claims source='sanskar', must be from InsightBridge",
                severity="MEDIUM"
            )
    
    return True
```

### Observability Drift Detection

```python
class ObservabilityDriftDetector:
    """Monitors for observability authority violations."""
    
    def __init__(self):
        self.violations = []
    
    def check_no_direct_export(self, sanskar_output: Dict) -> bool:
        
        forbidden_exports = [
            "prometheus_push",
            "jaeger_send",
            "datadog_post",
            "stdout_metric",
            "file_metric_write"
        ]
        
        for export_method in forbidden_exports:
            if export_method in sanskar_output:
                self.violations.append({
                    "check": "direct_export",
                    "forbidden_method": export_method,
                    "trace_id": sanskar_output.get("trace_id")
                })
                return False
        
        return True
    
    def check_adapter_usage(self, adapter_chain_stats: Dict) -> bool:
        
        insightbridge_stats = adapter_chain_stats.get(
            "bucket_to_insightbridge", {}
        )
        
        if insightbridge_stats.get("metrics_emitted", 0) == 0:
            self.violations.append({
                "check": "adapter_bypass",
                "detail": "No telemetry emitted through proper adapter"
            })
            return False
        
        return True
```

---

## 3. TESTING DRIFT CHECKS

### Definition

**Testing Drift** = Self-testing becoming test governance (setting rules, not verifying them).

### Drift Signals

#### Signal 1: Tests that modify enforcement rules

```python
def check_test_enforcement_mutation(test_output: Dict) -> bool:
    
    forbidden_test_mutations = {
        "set_enforcement_policy",
        "override_boundary_check",
        "disable_authority_detector",
        "modify_governance_rule"
    }
    
    actual_actions = set(test_output.get("actions", []))
    if forbidden_test_mutations & actual_actions:
        raise TestDriftViolation(
            detail="Tests attempted to modify enforcement rules"
        )
    
    return True
```

#### Signal 2: Tests creating backdoors

```python
def check_no_test_backdoors(test_suite: Dict) -> bool:
    
    backdoor_patterns = [
        "direct_access_to",
        "bypass_adapter",
        "skip_validation",
        "mock_enforcement"
    ]
    
    for pattern in backdoor_patterns:
        if pattern in str(test_suite):
            raise TestDriftViolation(
                detail=f"Test contains backdoor pattern: {pattern}"
            )
    
    return True
```

### Testing Drift Detection

```python
class TestingDriftDetector:
    
    
    def check_test_scope(self, test_name: str, test_config: Dict) -> bool:
        
        allowed_test_types = {
            "verify_contract_validation",
            "verify_trace_continuity",
            "verify_replay_determinism",
            "verify_boundary_enforcement",
            "verify_recovery_behavior"
        }
        
        test_type = test_config.get("type")
        if test_type not in allowed_test_types:
            return False
        
        return True
    
    def check_no_authority_manipulation(self, test_code: str) -> bool:
        
        forbidden_operations = [
            "set_authority",
            "override_boundary",
            "grant_permission",
            "modify_ceiling"
        ]
        
        for op in forbidden_operations:
            if op in test_code:
                return False
        
        return True
```

---

## 4. REPLAY DRIFT CHECKS

### Definition

**Replay Drift** = Replay output differs from original execution (non-deterministic behavior).

### Drift Signals

#### Signal 1: Output hash mismatch

```python
def check_replay_hash_mismatch(
    original_hash: str,
    replayed_hash: str,
    trace_id: str
) -> bool:
    """Detect if replayed output differs from original."""
    if original_hash != replayed_hash:
        raise ReplayDriftViolation(
            drift_type="output_divergence",
            detail=f"Replayed output hash mismatch",
            trace_id=trace_id,
            original_hash=original_hash,
            replayed_hash=replayed_hash,
            severity="CRITICAL"
        )
    
    return True
```

#### Signal 2: Timing variance beyond threshold

```python
def check_replay_timing_variance(
    original_timing_ms: float,
    replayed_timing_ms: float,
    max_variance_percent: float = 10.0
) -> bool:
    """Detect if replay timing deviates significantly."""
    variance_percent = abs(replayed_timing_ms - original_timing_ms) / original_timing_ms * 100
    
    if variance_percent > max_variance_percent:
        raise ReplayDriftViolation(
            drift_type="timing_divergence",
            detail=f"Replay timing variance {variance_percent}% > threshold {max_variance_percent}%",
            severity="MEDIUM"
        )
    
    return True
```

### Replay Drift Detection

```python
class ReplayDriftDetector:
    
    def __init__(self):
        self.drift_events = []
    
    def verify_replay_determinism(
        self,
        trace_id: str,
        original_output: Dict,
        replayed_output: Dict
    ) -> bool:
        
        original_hash = hashlib.sha256(
            json.dumps(original_output, sort_keys=True).encode()
        ).hexdigest()
        
        replayed_hash = hashlib.sha256(
            json.dumps(replayed_output, sort_keys=True).encode()
        ).hexdigest()
        
        if original_hash != replayed_hash:
            self.drift_events.append({
                "trace_id": trace_id,
                "drift_type": "output_divergence",
                "original_hash": original_hash,
                "replayed_hash": replayed_hash
            })
            return False
        
       
        original_ranking = original_output.get("ranking", [])
        replayed_ranking = replayed_output.get("ranking", [])
        
        if original_ranking != replayed_ranking:
            self.drift_events.append({
                "trace_id": trace_id,
                "drift_type": "ranking_divergence",
                "original_ranking": original_ranking,
                "replayed_ranking": replayed_ranking
            })
            return False
        
        return True
    
    def get_drift_report(self) -> Dict:
        return {
            "total_replays_tested": len(self.drift_events),
            "drifts_detected": len(self.drift_events),
            "drift_events": self.drift_events
        }
```

---

## 5. HIDDEN AUTHORITY CHECK

### Definition

**Hidden Authority** = SANSKAR performing restricted operations secretly without declaring them.

### Check Mechanism

```python
class HiddenAuthorityDetector:
    
    
    def check_hidden_operations(self, sanskar_output: Dict) -> bool:
        
        declared_operations = set(sanskar_output.get("declared_operations", []))
        
       
        actual_operations = self._infer_actual_operations(sanskar_output)
        
        
        hidden_operations = actual_operations - declared_operations
        
        if hidden_operations:
            raise HiddenAuthorityViolation(
                detail=f"Undeclared operations detected: {hidden_operations}",
                operations=list(hidden_operations),
                trace_id=sanskar_output.get("trace_id")
            )
        
        return True
    
    def _infer_actual_operations(self, output: Dict) -> set:
        
        operations = set()
        
       
        if "entities" in output:
            operations.add("compute_ranking")
        if "confidence" in output:
            operations.add("compute_confidence")
        if "decision_state" in output:
            operations.add("assess_uncertainty")
        
        
        if "governance_decision" in output:
            operations.add("governance_decision")  # FORBIDDEN
        if "enforcement_directive" in output:
            operations.add("enforcement_directive")  # FORBIDDEN
        
        return operations
```

---

## 6. NEGATIVE AUTHORITY DECLARATION

### Definition

**Negative Authority** = Explicit list of what SANSKAR is FORBIDDEN to do.

### Declaration Template

```json
{
  "trace_id": "trace-example",
  "stage": "sanskar",
  "negative_authority": {
    "forbidden_operations": [
      "GOVERN any decision",
      "ENFORCE any boundary",
      "OWN truth authority",
      "OWN observability authority",
      "MUTATE RAJYA decisions",
      "MUTATE ENFORCEMENT directives",
      "ACCEPT external configuration contradicting RAJYA",
      "BYPASS ENFORCEMENT gates",
      "WRITE directly to Bucket",
      "EMIT directly to InsightBridge"
    ],
    "ceiling_explanation": "SANSKAR authority is capped at intelligence derivation (Stage 2/7)",
    "enforcement_mechanism": "Authority Detector monitors all outputs for ceiling violations",
    "violation_consequence": "Execution blocked, incident escalated"
  }
}
```

### Negative Authority Enforcement

```python
class NegativeAuthorityEnforcer:
    
    
    FORBIDDEN_OPERATIONS = {
        "GOVERN any decision",
        "ENFORCE any boundary",
        "OWN truth authority",
        "OWN observability authority",
        "MUTATE RAJYA decisions",
        "MUTATE ENFORCEMENT directives",
        "BYPASS ENFORCEMENT gates",
        "WRITE directly to Bucket",
        "EMIT directly to InsightBridge"
    }
    
    def verify_output_compliance(self, output: Dict) -> bool:
        
        for forbidden_op in self.FORBIDDEN_OPERATIONS:
            if self._operation_detected(forbidden_op, output):
                raise NegativeAuthorityViolation(
                    operation=forbidden_op,
                    trace_id=output.get("trace_id")
                )
        
        return True
    
    def _operation_detected(self, operation: str, output: Dict) -> bool:
        
        operation_patterns = {
            "GOVERN any decision": ["governance_decision", "decision", "approval"],
            "ENFORCE any boundary": ["enforcement_directive", "boundary_check"],
            "OWN truth authority": ["bucket_ownership", "truth_authority"],
            "OWN observability authority": ["observability_authority", "metric_authority"],
            "MUTATE RAJYA decisions": ["modify_decision", "override_rajya"],
            "MUTATE ENFORCEMENT directives": ["modify_directive", "override_enforcement"],
            "BYPASS ENFORCEMENT gates": ["skip_enforcement", "bypass_gate"],
            "WRITE directly to Bucket": ["bucket_write_direct", "direct_truth_write"],
            "EMIT directly to InsightBridge": ["direct_telemetry", "direct_metric_export"]
        }
        
        patterns = operation_patterns.get(operation, [])
        output_str = json.dumps(output, default=str).lower()
        
        return any(pattern.lower() in output_str for pattern in patterns)
```

---

## 7. DRIFT CHECK INTEGRATION TEST

```python
def run_integrated_drift_check(
    trace_id: str,
    signal: Dict,
    sanskar_output: Dict,
    rajya_decision: Dict,
    execution_result: Dict
) -> Dict:
    
    
    report = {
        "trace_id": trace_id,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    
    try:
        auth_detector = AuthorityDriftDetector()
        auth_detector.check_stage_output("sanskar", sanskar_output)
        auth_detector.check_stage_output("rajya", rajya_decision)
        report["checks"]["authority_drift"] = {
            "status": "PASS",
            "violations": []
        }
    except DriftViolation as dv:
        report["checks"]["authority_drift"] = {
            "status": "FAIL",
            "violations": [str(dv)]
        }
    
   
    try:
        obs_detector = ObservabilityDriftDetector()
        obs_detector.check_no_direct_export(sanskar_output)
        report["checks"]["observability_drift"] = {
            "status": "PASS",
            "violations": obs_detector.violations
        }
    except Exception as e:
        report["checks"]["observability_drift"] = {
            "status": "FAIL",
            "violations": [str(e)]
        }
    
    
    try:
        neg_enforcer = NegativeAuthorityEnforcer()
        neg_enforcer.verify_output_compliance(sanskar_output)
        report["checks"]["negative_authority"] = {
            "status": "PASS"
        }
    except NegativeAuthorityViolation as nav:
        report["checks"]["negative_authority"] = {
            "status": "FAIL",
            "violation": str(nav)
        }
    
   
    report["overall"] = "PASS" if all(
        c.get("status") == "PASS" for c in report["checks"].values()
    ) else "FAIL"
    
    return report
```

---

## NEXT PHASE

**Phase 5 — Deployment/Testing:** Create 5-10 minute deterministic self-test with at least 6 failure mode scenarios and recovery verification.

