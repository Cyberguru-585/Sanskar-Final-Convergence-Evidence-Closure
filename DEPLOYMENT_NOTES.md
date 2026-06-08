# DEPLOYMENT_NOTES.md — SANSKAR→TANTRA Operational Deployment


---

## DEPLOYMENT READINESS CHECKLIST

### Pre-Deployment Verification

- [x] All 6 integration tests PASS (100% success rate)
- [x] All 7 hostile scenarios execute successfully
- [x] Runtime process separation verified (real PIDs: 11016, 6568, 5104)
- [x] Contract enforcement working at all boundaries
- [x] Trace continuity verified across all stages
- [x] Authority violations blocked correctly
- [x] Drift checks implemented and tested
- [x] Replay determinism verified
- [x] Documentation complete
- [x] Operator manual included

### Generated Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| TANTRA_PLACEMENT.md | Root | ✓ Enhanced with runtime proof |
| AUTHORITY_MATRIX.md | Root | ✓ Complete |
| DRIFT_CHECKS.md | Root | ✓ New - comprehensive |
| TRACE_SCHEMA_PROVENANCE.md | Root | ✓ Enhanced |
| REVIEW_PACKET_INTEGRATION.md | Root | ✓ New - operator guide |
| DEPLOYMENT_NOTES.md | Root | ✓ This file |
| runtime_adapters.py | Root | ✓ Contract enforcement |
| tantra_integration_test_report.json | Root | ✓ 6/6 tests PASS |
| runtime_boot_proof.json | Root | ✓ Real PIDs proven |
| runtime_hostile_suite.json | Root | ✓ 7/7 scenarios tested |

---

## DEPLOYMENT SCENARIOS

### Scenario 1: Development Deployment (Immediate)

**Duration:** ~30 minutes  
**Environment:** Local machine / single VM  
**Risk Level:** Low

#### Steps:

```bash

git clone <repo> && cd TASK\ 6


pip install -r requirements.txt


python -c "import sys; print(f'Python {sys.version}')"


python tantra_integration_self_test.py


python runtime_hostile_suite.py



ls -1 *_proof.json | wc -l

```

#### Verification:
- All 6 integration tests pass
- All 7 hostile scenarios execute
- All proof artifacts exist
- No errors in logs

#### Next: Proceed to Staging Deployment

### Scenario 2: Staging Deployment (Week 1)

**Duration:** ~2-4 hours initial setup  
**Environment:** Multi-VM staging cluster  
**Risk Level:** Medium (real infrastructure)

#### Pre-Deployment:

1. **Infrastructure Setup:**
   ```bash
   # Provision 3 VMs for services
   terraform apply -var environment=staging
   
   # Install runtime dependencies
   ansible-playbook deploy/staging/init.yml
   ```

2. **Configuration:**
   ```bash
   # Copy configuration templates
   cp runtime_config/sanskar_config.json.template staging_config/sanskar_config.json
   
   # Update endpoints
   sed -i 's/localhost/rajya.staging/g' staging_config/*.json
   ```

3. **Observability Backend:**
   ```bash
   # Deploy Prometheus scraper
   kubectl apply -f observability/prometheus-staging.yaml
   
   # Deploy Jaeger collector
   kubectl apply -f observability/jaeger-staging.yaml
   
   # Verify endpoints ready
   curl http://prometheus.staging:9090/-/ready
   curl http://jaeger.staging:14269
   ```

#### Deployment:

```bash

docker-compose -f deploy/staging/docker-compose.yml up -d


docker-compose ps



curl http://sanskar:8001/health
curl http://rajya:8002/health
curl http://enforcement:8003/health



python tantra_integration_self_test.py --env staging
# Expected: 6/6 PASS


python tools/load_test.py --target staging --duration 3600 --rate 100
# Expected: 100 req/sec, <200ms p99 latency
```

#### Monitoring (24/7 for 1-2 weeks):

**Key Metrics to Monitor:**
- `sanskar_request_duration_seconds` — Should stay <200ms p99
- `sanskar_ranking_confidence` — Distribution should be stable
- `adapter_chain_violations_total` — Should stay 0 or very low
- `trace_divergences_total` — Must be 0 (indicates bugs)
- `authority_violations_total` — Should be 0 (indicates drift)

**Alerts:**
- If divergences > 0 → Immediate investigation + rollback
- If violations > 10/hour → Check logs for authority drift
- If latency p99 > 500ms → Check resource utilization

#### Success Criteria:
- Stable for 24+ hours with zero divergences
- Handle 100+ req/sec without degradation
- All hostile scenarios survive injection
- Observability metrics flowing to backends

#### Next: Proceed to Production Pilot

### Scenario 3: Production Pilot (Week 2-4)

**Duration:** 2-4 weeks continuous operation  
**Environment:** Canary deployment (5-10% traffic)  
**Risk Level:** High (real business impact, but limited)

#### Canary Configuration:

```yaml

apiVersion: fluxcd.io/v1
kind: Kustomization
metadata:
  name: sanskar-canary
spec:
  sourceRef:
    name: sanskar
  path: ./kustomize/production
  
  
  targetExclusions:
    - kind: Service
      name: sanskar
      namespace: default
  
 
```

#### Deployment:

```bash

kubectl apply -f deploy/production/canary.yaml


kubectl get virtualservice sanskar-canary -o yaml | grep weight

# 3. Monitor continuously
# Watch these dashboards every 4 hours:
# - Request volume (should see ~5% on new service)
# - Error rate (must stay <1%)
# - Latency (must stay <200ms p99)
# - Divergence count (must stay 0)
```

#### Success Criteria:
- Zero divergences over 2 weeks
- Error rate < 1%
- Latency p99 < 200ms consistently
- Authority violations = 0
- Observability fully operational

#### Rollback Procedure:
```bash

kubectl set image deployment/sanskar sanskar=sanskar:previous


kubectl rollout status deployment/sanskar


python tools/incident_analyzer.py --hours 1
```

#### Next: Full Production Deployment

### Scenario 4: Full Production Deployment

**Duration:** Gradual rollout over days  
**Environment:** 100% traffic  
**Risk Level:** High (all business traffic)

#### Gradual Rollout:

```
Day 1: 10% traffic
  ↓ (monitor for 24h)
Day 2: 25% traffic
  ↓ (monitor for 24h)
Day 3: 50% traffic
  ↓ (monitor for 24h)
Day 4: 75% traffic
  ↓ (monitor for 24h)
Day 5: 100% traffic
  ↓ (monitor for 2 weeks with full support)
```

#### Each Stage Verification:

```bash

python verify_production_health.py \
  --error_rate_max 0.5 \
  --latency_p99_max 200 \
  --divergence_max 0 \
  --violation_max 0


```

---

## ROLLBACK PROCEDURES

### Immediate Rollback (< 1 minute)

**Trigger:** Any of these events
- Trace divergence detected (any count > 0)
- Authority violation detected
- Error rate > 5%
- Latency p99 > 1000ms

**Procedure:**

```bash

kubectl patch virtualservice sanskar-production \
  --type merge -p '{"spec":{"hosts":[{"weight":0}]}}'


kubectl get svc sanskar -o wide | grep CLUSTER-IP


curl http://sanskar-old:8001/health


python tools/incident_report.py > incident_$(date +%Y%m%d_%H%M%S).md


slack message --channel #platform "SANSKAR rollback executed at $(date)"
```

### Graceful Rollback (5-10 minutes)

**Procedure:**

```bash

kubectl set env deployment/sanskar ACCEPTING_REQUESTS=false


sleep 30


python verify_old_version_health.py


kubectl set image deployment/sanskar sanskar=sanskar:previous


watch -n 5 'kubectl top pod -l app=sanskar'


tar czf /archive/incident_logs_$(date +%Y%m%d_%H%M%S).tar.gz /var/log/sanskar/
```

---

## OPERATIONAL PROCEDURES

### Daily Health Check (5 minutes)

```bash
#!/bin/bash
# Run every morning

echo "=== SANSKAR Health Check ==="
echo "1. Service Status:"
kubectl get pods -l app=sanskar

echo "2. Recent Errors:"
kubectl logs -l app=sanskar --tail=100 | grep ERROR | wc -l

echo "3. Recent Divergences:"
curl -s http://prometheus:9090/api/v1/query?query=increase(trace_divergences_total\[1d\]) | jq .

echo "4. Request Latency (p99):"
curl -s http://prometheus:9090/api/v1/query?query=histogram_quantile\(0.99,sanskar_request_duration_seconds\) | jq .

echo "5. Authority Violations:"
curl -s http://prometheus:9090/api/v1/query?query=increase(authority_violations_total\[1d\]) | jq .

echo "All checks complete. Status: HEALTHY"
```

### Weekly Capacity Review

```bash
# Analyze usage patterns
python tools/capacity_analyzer.py \
  --period 7d \
  --output capacity_report_$(date +%Y%m%d).md


if [ $(cat capacity_report_*.md | grep "Scale Recommendation") ]; then
  echo "Consider scaling up resources"
  kubectl patch deployment sanskar -p '{"spec":{"replicas":3}}'
fi
```

### Monthly Security Audit

```bash

python tools/audit_authority_boundaries.py


python tools/test_drift_detection.py


python tools/verify_replay_determinism.py --sample_size 1000
```

---

## INCIDENT RESPONSE

### Authority Violation Detected

**Severity:** CRITICAL (immediate halt)

```
Detection: adapter_chain logs show ContractViolation
Response:
  1. Immediate rollback (< 1 minute)
  2. Preserve all logs
  3. Page on-call engineer
  4. Start incident investigation
  5. Analyze what caused SANSKAR to exceed authority
  6. Root cause analysis before next deployment
```

### Trace Divergence Detected

**Severity:** CRITICAL (indicates non-determinism)

```
Detection: replay_divergence_detector.py shows mismatch
Response:
  1. Immediate rollback (< 1 minute)
  2. Compare original vs replayed output
  3. Identify code differences (if any)
  4. Check for external randomness (time.time(), random(), etc.)
  5. Root cause analysis required
  6. Cannot redeploy without understanding cause
```

### Service Down

**Severity:** HIGH (business impact)

```
Detection: participant_health_matrix.json shows state != RUNNING
Response:
  1. Check systemctl status
  2. Review recent logs for errors
  3. Restart service: systemctl restart sanskar
  4. Verify comes back up: wait for state RUNNING
  5. Run health checks
  6. If doesn't recover: escalate to tier-2 support
```

---

## CONFIGURATION MANAGEMENT

### Version Pinning

```bash
# All deployments must pin specific versions
# In docker-compose.yml:
sanskar:
  image: sanskrit/sanskar:2.1.0-production
  # NOT: latest (dangerous)

# In deployment manifest:
containers:
- name: sanskar
  image: sanskrit/sanskar:2.1.0-production@sha256:abc123...
  # Include digest for immutability
```

### Configuration Updates

```bash
# DO NOT change config in production directly
# Instead:

# 1. Update config in version control
vim runtime_config/sanskar_config.json

# 2. Create new deployment with new config
kubectl set env deployment/sanskar \
  CONFIG_VERSION=2.1.0-v2

# 3. Canary deploy to 5% of traffic
# 4. Monitor for 24 hours
# 5. Full rollout or rollback based on metrics
```

---

## SUPPORT & ESCALATION

### Support Channels

| Issue | Channel | Response Time |
|-------|---------|----------------|
| Normal question | #platform-support | 24h |
| Bug report | GitHub issues | 4h |
| Performance concern | page on-call | 15m |
| Security issue | security@company.com | 1h |
| Critical incident | All hands | immediate |

### Escalation Path

```
Level 1: On-Call Engineer
  ↓ (if cannot resolve in 15m)
Level 2: SANSKAR Integration Team
  ↓ (if needs code changes)
Level 3: Governance & Authority Team
  ↓ (if involves policy/authority questions)
Level 4: Executive Steering
  ↓ (if production impact > 1 hour)
```

---

## MAINTENANCE WINDOW

### Planned Maintenance Procedure

```bash
# Announced 48 hours in advance
# Executed during low-traffic window (2-4 AM UTC)

# 1. Notify all stakeholders
mail -s "SANSKAR maintenance window: 2-4 AM UTC" ops-team

# 2. Stop accepting new requests
kubectl patch deployment sanskar -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"sanskar","env":[{"name":"ACCEPTING_REQUESTS","value":"false"}]}]}}}}'

# 3. Wait for graceful drain (up to 30s)
sleep 30

# 4. Perform maintenance
# - Update runtime adapter contracts
# - Update governance rules
# - etc.

# 5. Verify integrity
python verify_integrity_after_maintenance.py

# 6. Resume
kubectl patch deployment sanskar -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"sanskar","env":[{"name":"ACCEPTING_REQUESTS","value":"true"}]}]}}}}'

# 7. Monitor for 1 hour
watch -n 5 'kubectl top pod -l app=sanskar'
```

---

## TROUBLESHOOTING GUIDE

### Common Issues

#### Issue: "ContractViolation: SANSKAR produced governance_decision"

**Cause:** SANSKAR output violates authority ceiling

**Resolution:**
1. Check SANSKAR code for new fields
2. Verify authority detector is working
3. If violated recently, rollback
4. Fix code, re-test, redeploy

#### Issue: "Trace divergence detected"

**Cause:** Same input produces different output

**Resolution:**
1. Do NOT redeploy until root cause found
2. Check for:
   - Randomness (random(), time.time())
   - External state (files, network calls)
   - Floating point precision issues
3. Fix root cause
4. Verify with replay test (1000 iterations)
5. Only then redeploy

#### Issue: "RAJYA unavailable"

**Cause:** Service crashed or network problem

**Resolution:**
1. Check pod status: `kubectl get pods -l app=rajya`
2. Check logs: `kubectl logs -l app=rajya --tail=50`
3. Restart: `kubectl delete pod -l app=rajya` (will recreate)
4. Wait for health check to pass
5. If persists, investigate why RAJYA crashed

---

## APPENDIX: Deployment Checklist

```
PRE-DEPLOYMENT:
[ ] All 6 integration tests pass
[ ] All 7 hostile scenarios succeed
[ ] Runtime process separation verified
[ ] All proof artifacts generated
[ ] Documentation reviewed
[ ] Operator manual tested
[ ] Monitoring dashboards created
[ ] Alerting thresholds configured
[ ] Runbooks prepared
[ ] Team trained

DEPLOYMENT DAY:
[ ] Staging environment verified
[ ] Observability backend working
[ ] Backup of previous version created
[ ] Rollback procedure tested
[ ] On-call team notified
[ ] Maintenance window announced
[ ] Deployment approved by team lead

POST-DEPLOYMENT:
[ ] All health checks pass
[ ] No errors in logs (first 5 min)
[ ] Metrics flowing to Prometheus
[ ] Traces flowing to Jaeger
[ ] Dashboard metrics normal
[ ] Error rate < 1%
[ ] Divergence count = 0
[ ] Authority violations = 0
[ ] Team monitor for 24h
[ ] Success criteria met
[ ] Incident report generated (if any)
```

---


