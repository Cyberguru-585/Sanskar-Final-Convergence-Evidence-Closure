# FAQ.md

# Frequently Asked Questions - SANSKAR Ecosystem

---

## General Questions

### Q: What is SANSKAR?
**A:** SANSKAR is a distributed intelligence-governance system that separates:
- **SANSKAR** (intelligence layer) - produces rankings
- **RAJYA** (governance layer) - validates and decides
- **ENFORCEMENT** (boundary layer) - enforces fail-closed behavior

### Q: Is SANSKAR ready for production?
**A:** Yes. As of June 1, 2026:
-  All 8 self-tests pass
-  All 7 hostile scenarios survived
-  Governance boundaries verified
-  Deployment validated
-  Status: READY_FOR_PRODUCTION

### Q: How long does it take to start up?
**A:** Cold boot (full startup) takes ~0.8-1.0 seconds. Warm restart (preserving state) takes ~0.5 seconds.

### Q: What's the deployment profile I should use?
**A:** 
- **Development:** Local development and debugging
- **Staging:** Pre-production testing
- **Production:** Live traffic (recommended for production use)

---

## Architecture Questions

### Q: Why is SANSKAR not a "decision maker"?
**A:** By design, SANSKAR is a **bounded intelligence producer**, not a decision authority. This separates:
- Intelligence generation (SANSKAR)
- Governance authority (RAJYA)

This prevents intelligent systems from becoming policy-makers.

### Q: What does "governance authority" mean?
**A:** RAJYA has exclusive authority to:
- Validate policies
- Make binding decisions
- Override intelligence recommendations
- Set fail-closed defaults

Only RAJYA can approve execution.

### Q: What if SANSKAR and RAJYA disagree?
**A:** RAJYA wins. RAJYA is the governance authority. If they disagree, the system uses replay-based arbitration to understand both sides, then RAJYA's governance authority prevails.

### Q: What is "fail-closed"?
**A:** Fail-closed means: if the system is uncertain, it defaults to **DENY** (no action). This prevents accidental authorizations during failures.

---

## Operational Questions

### Q: How do I check if the system is healthy?
**A:** Run the health check:
```bash
python service_registry.py
```
This shows:
- All 3 services registered
- Health percentage (should be 100%)
- Endpoint status

### Q: What should I do if a service crashes?
**A:** The system recovers automatically:
1. Health check detects the crash
2. Service restarts (if auto-restart enabled)
3. State is replayed from checkpoint
4. System resumes operation

Recovery time: ~0.4 seconds

### Q: How do I safely restart the system?
**A:** Use warm restart:
```bash
python deployment_validator.py
```
This performs:
1. Graceful shutdown (drains requests)
2. State checkpoint
3. Restart with state restored
4. Health validation

Time: ~0.5 seconds

### Q: Can I run SANSKAR on Windows?
**A:** Yes, all code is cross-platform Python. Use PowerShell instead of bash for commands.

### Q: What ports does SANSKAR use?
**A:** 
- SANSKAR: 8001
- RAJYA: 8002
- ENFORCEMENT: 8003

These must be available (not in use by other services).

---

## Governance Questions

### Q: Can SANSKAR make governance decisions?
**A:** No. SANSKAR is blocked at runtime from governance actions. Any attempt is caught and logged as a violation.

### Q: Can RAJYA be bypassed?
**A:** No. RAJYA is the exclusive governance authority. No other service can override RAJYA decisions.

### Q: What happens if governance is violated?
**A:** The violation is:
1. **Detected** by governance monitoring (Phase 4)
2. **Logged** with event_id and timestamp
3. **Blocked** - the illegal action is rejected
4. **Escalated** - incident alert triggered

### Q: Is trace_id immutable?
**A:** Yes. Trace_id must remain unchanged across all ecosystem boundaries. If it's mutated, the system detects it as a critical violation.

### Q: How do I verify governance compliance?
**A:** Run the governance audit:
```bash
python governance_runtime_monitor.py
```
This tests:
- Authority boundaries
- Boundary drift
- Trace integrity
- Constitutional alignment

---

## Testing Questions

### Q: How do I run the self-tests?
**A:** See SELF_TESTING_PACKET.md. All 8 tests can be run in 5-10 minutes:
```bash
python service_registry.py              
python runtime_service_bootstrap.py     
python live_bhiv_integration_chain.py   
python runtime_hostile_suite.py         
python governance_runtime_monitor.py    
python deployment_validator.py          

```

### Q: What does "hostile scenario" mean?
**A:** A hostile scenario is a simulated failure (e.g., network partition, service crash, schema mismatch). The system must survive and recover.

### Q: Can the system survive all 7 hostile scenarios?
**A:** Yes. Phase 3 proves 7/7 scenarios survived with recovery proof.

### Q: What if a test fails?
**A:** See SELF_TESTING_PACKET.md → ROOT CAUSE ANALYSIS section for troubleshooting each test.

---

## Integration Questions

### Q: How does SANSKAR integrate with BHIV?
**A:** SANSKAR participates in the BHIV ecosystem through:
- **RAJYA:** Governance validation interface
- **Bucket:** Persistence integration (3 replicas)
- **InsightBridge:** Telemetry emission
- **Trace continuity:** Immutable trace_id across all boundaries

See cross_ecosystem_execution_proof.json for proof.

### Q: What is trace continuity?
**A:** Trace continuity means the same trace_id flows through all ecosystem boundaries:
```
SANSKAR → RAJYA → Bucket → InsightBridge
  ↓         ↓        ↓          ↓
trace-X   trace-X  trace-X   trace-X
```
All are identical (immutable). This enables end-to-end tracing.

### Q: What if InsightBridge is unavailable?
**A:** Graceful degradation:
- System continues operating
- Telemetry is reduced (fewer collectors)
- Decisions are still valid
- Recovery: ~0 seconds (no wait)

---

## Security Questions

### Q: Are there security boundaries?
**A:** Yes. Authority boundaries are the primary security model:
- SANSKAR: NO authority (intelligence only)
- RAJYA: FULL authority (governance only)
- ENFORCEMENT: Fail-closed enforcement only

### Q: What if someone tries to modify SANSKAR code?
**A:** Drift monitoring detects:
1. Any undeclared actions
2. Boundary violations
3. Authority mismatches

Violations trigger immediate alerts.

### Q: What's the difference between "liveness" and "readiness"?
**A:** 
- **Liveness:** Service process is alive (hasn't crashed)
- **Readiness:** Service is ready to handle requests

A service can be alive but not ready (e.g., still initializing).

---

## Deployment Questions

### Q: What's the difference between cold boot and warm restart?
**A:**
- **Cold boot:** Full startup from scratch (~0.8s)
- **Warm restart:** Preserving state, faster (~0.5s)

Use warm restart in production when possible.

### Q: Can I upgrade SANSKAR without downtime?
**A:** Not with current architecture. You must:
1. Warm restart (graceful shutdown)
2. Deploy new code
3. Restart services

Total downtime: ~0.5 seconds (acceptable for most use cases).

### Q: What's the memory footprint?
**A:** Per profile:
- Development: 256MB × 3 services = 768MB total
- Staging: 512MB × 3 = 1.5GB total
- Production: 1024MB × 3 = 3GB total (multiply by 2 for replicas)

---

## Troubleshooting Questions

### Q: Port 8001 is already in use. What do I do?
**A:** Either:
1. Kill the existing process: `lsof -i :8001 | kill -9`
2. Or modify the port in governance_audit_contract.json

### Q: Services start but show "[CAUGHT] SANSKAR governance: Not authorized"
**A:** This is expected! The governance audit is testing that SANSKAR is blocked from governance. This is correct behavior.

### Q: My test took longer than 10 minutes.
**A:** SELF_TESTING_PACKET.md targets 5-10 minutes. If slower:
- Check system load: `top` or Task Manager
- Verify no other services on ports 8001-8003
- Run only one test at a time

### Q: I see "[DRIFT] SANSKAR performed undeclared action"
**A:** This indicates a boundary drift violation:
1. Check the action in the log
2. Verify it's declared in authority_boundary_map.md
3. If undeclared, investigate code changes

---

## References

| Question Type | Reference Document |
|---------------|-------------------|
| Operational guidance | operator_manual.md |
| Governance & boundaries | authority_boundary_map.md |
| Testing | SELF_TESTING_PACKET.md |
| Deployment | deployment_validation_proof.json |
| Architecture | FINAL_REVIEW_PACKET.md |
| Integration | cross_ecosystem_execution_proof.json |

---

## Still have questions?

- **Operational issues:** Refer to operator_manual.md
- **Governance questions:** Refer to authority_boundary_map.md
- **Testing issues:** Refer to SELF_TESTING_PACKET.md
- **Design questions:** Refer to FINAL_REVIEW_PACKET.md

---
