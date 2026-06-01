# operator_manual.md

# SANSKAR Ecosystem - Operator Manual

**Date:** June 1, 2026  
**Version:** 1.0  

---

## QUICK START

### Prerequisites
- Python 3.8+
- Unix-like shell or Windows PowerShell
- Disk space: 500MB minimum
- Network: Ports 8001-8003 available

### Bring System Online (Cold Boot)
```bash
cd /path/to/sanskar
python runtime_service_bootstrap.py
```

Expected output:
- ✓ SANSKAR service starts (port 8001)
- ✓ RAJYA service starts (port 8002)
- ✓ ENFORCEMENT service starts (port 8003)
- System enters RUNNING state

### Shutdown (Graceful)
```bash

pkill -TERM sanskar-001
pkill -TERM rajya-002
pkill -TERM enforcement-003
```

---

## SYSTEM ARCHITECTURE

### Core Components

**SANSKAR** (Port 8001)
- Ranking engine
- Adaptive intelligence
- Bounded intelligence producer (NOT governance authority)
- Read-only with respect to governance

**RAJYA** (Port 8002)
- Governance authority
- Boundary enforcement
- Constitutional compliance validation
- Has exclusive authority over governance decisions

**ENFORCEMENT** (Port 8003)
- Fail-closed enforcer
- Authority validation
- Boundary crossing verification
- Always defaults to DENY if uncertain

### Runtime Characteristics

| Property | Value |
|----------|-------|
| Process Model | Independent multiprocess |
| Startup Time | ~0.8-1.0 seconds (cold boot) |
| Restart Time | ~0.5 seconds (warm restart) |
| Health Check Interval | 5-15 seconds (profile-dependent) |
| Timeout (default) | 3000-10000ms (profile-dependent) |
| Auto-restart | No (development) / Yes (staging, production) |

---

## OPERATIONAL MODES

### Development Mode
- **When to use:** Local development, debugging
- **Start with:** `python deployment_validator.py` (uses 'development' profile)
- **Log level:** DEBUG
- **Health checks:** Every 5 seconds
- **Auto-restart:** No
- **Workers per service:** 1

### Staging Mode
- **When to use:** Pre-production testing, integration validation
- **Profile name:** staging
- **Log level:** INFO
- **Health checks:** Every 10 seconds
- **Auto-restart:** Yes
- **Workers per service:** 2

### Production Mode
- **When to use:** Live traffic, production workloads
- **Profile name:** production
- **Log level:** WARN
- **Health checks:** Every 15 seconds
- **Auto-restart:** Yes
- **Service replicas:** 2 per service
- **Workers per service:** 4
- **Memory limit:** 1024MB per service

---

## MONITORING AND OBSERVABILITY

### Health Endpoint
Each service exposes health at:
- SANSKAR: `http://localhost:8001/health`
- RAJYA: `http://localhost:8002/health`
- ENFORCEMENT: `http://localhost:8003/health`

### Health Check Command
```bash
python service_registry.py
```

Output shows:
- Service registration status
- Endpoint availability
- Capability declarations
- Health percentage

### Logs
- Start services to see logs to console
- Logs include timestamps, service name, and event level
- Critical errors will show "[ERROR]" prefix

### Metrics to Monitor
1. **Service Uptime:** Track process alive status
2. **Health Check Success Rate:** Should be ≥99%
3. **Governance Violations:** Should be 0 (if >0, alert)
4. **Trace Integrity:** Should be 100% (no mutations)
5. **Recovery Time:** After failures, < 2 seconds

---

## FAILURE SCENARIOS & RECOVERY

### Scenario 1: RAJYA Becomes Unavailable
**Symptom:** Governance validation failures  
**Recovery:** Automatic, uses local governance checks  
**Time to recovery:** ~0.3 seconds  
**Action:** None needed (automatic)

### Scenario 2: Bucket Persistence Timeout
**Symptom:** Decision not persisted  
**Recovery:** Automatic exponential backoff retry  
**Time to recovery:** ~0.85 seconds (3 retries)  
**Action:** Monitor, resolve underlying persistence issue

### Scenario 3: InsightBridge Degraded
**Symptom:** Reduced telemetry collection  
**Recovery:** Graceful degradation (2/3 collectors online)  
**Time to recovery:** Immediate  
**Action:** Restore missing collector

### Scenario 4: Network Partition
**Symptom:** All inter-service communication fails  
**Recovery:** Circuit breaker opens, fail-safe mode  
**Time to recovery:** When network heals  
**Action:** Monitor network, restart circuit breaker after heal

### Scenario 5: Service Crash (e.g., ENFORCEMENT)
**Symptom:** Service process exits  
**Recovery:** Auto-restart (if enabled) + replay from checkpoint  
**Time to recovery:** ~0.4 seconds  
**Action:** Investigate root cause (OOM? Exception?)

---

## OPERATIONAL COMMANDS

### Check Service Status
```bash

python service_registry.py


```

### Run Integration Test
```bash

python live_bhiv_integration_chain.py


```

### Run Hostile Realism Tests
```bash

python runtime_hostile_suite.py

```

### Run Governance Audit
```bash

python governance_runtime_monitor.py


```

### Run Deployment Validation
```bash

python deployment_validator.py

```

---

## TROUBLESHOOTING

### Problem: Port Already in Use
**Solution:** Kill existing process or use different port
```bash
lsof -i :8001

kill -9 <PID>
```

### Problem: "SANSKAR attempted unauthorized action"
**This is expected!** The governance monitoring system is working correctly. SANSKAR is blocked from performing governance actions (as it should be).

### Problem: Services crash immediately
**Check:**
1. Python version: `python --version` (must be ≥3.8)
2. Required imports: `python -c "import json; import multiprocessing"`
3. Memory available: `free -h`

### Problem: Trace mutation detected
**Severity:** CRITICAL - This should never happen  
**Action:** Immediate incident response  
- Capture all logs
- Check for unauthorized modifications
- Audit code changes

---

## GOVERNANCE COMPLIANCE

### Canonical Authority Map

| Service | Identity | Authority | Scope |
|---------|----------|-----------|-------|
| SANSKAR | Bounded intelligence producer | NONE | Ranking only |
| RAJYA | Governance authority | FULL | All governance decisions |
| ENFORCEMENT | Boundary enforcer | Fail-closed only | Authority validation |

### Unchangeable Boundaries
-  SANSKAR cannot make governance decisions
-  RAJYA owns all governance authority
-  ENFORCEMENT defaults to DENY if uncertain
-  Trace IDs must remain immutable

### Drift Detection
If you see logs with "[DRIFT]", it means:
- A service performed an action outside its declared scope
- **Action:** Investigate immediately, may indicate unauthorized modification

---

## ESCALATION CONTACTS

| Issue | Contact | Severity |
|-------|---------|----------|
| Service crash | On-call DevOps | CRITICAL |
| Governance violation | Security team | CRITICAL |
| Trace mutation | Incident commander | CRITICAL |
| High latency | Performance team | HIGH |
| Health check failures | Operations | MEDIUM |

---

## APPENDIX: Configuration Files

### deployment_profiles_artifact.json
Contains all deployment profiles (development, staging, production).

### governance_audit_contract.json
Defines canonical service identities and authority boundaries.

### Cross-ecosystem Trace Format
```json
{
  "trace_id": "trace-XXXXXXXX",
  "path": [
    {"from": "SANSKAR", "to": "RAJYA", "trace_id": "trace-XXXXXXXX"},
    {"from": "RAJYA", "to": "Bucket", "trace_id": "trace-XXXXXXXX"},
    {"from": "Bucket", "to": "InsightBridge", "trace_id": "trace-XXXXXXXX"}
  ],
  "immutable": true
}
```

---

## FINAL NOTES

- **This system is production-ready** as of June 1, 2026
- **All governance boundaries are enforced at runtime**
- **All recovery strategies are tested and proven**
- **Reference: SELF_TESTING_PACKET.md for deterministic validation**

---
