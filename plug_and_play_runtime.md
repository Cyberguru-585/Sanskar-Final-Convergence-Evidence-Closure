# SANSKAR PLUG-AND-PLAY RUNTIME PACKAGE

**Version:** Phase 11 Execution  
**Date:** May 26, 2026  
**Status:** Production-Grade Deployment Package  

---

## OVERVIEW

Sanskar is now a **reusable, portable TANTRA ecosystem participant** with:

-  **Zero hardcoded local assumptions**
-  **Single launch/shutdown/health commands**
-  **Environment-agnostic configuration**
-  **Multiple deployment profiles** (development, integration, staging, production)
-  **Deterministic contract exchange** with immutable trace_id
-  **Production-grade observability** and health checks

---

## QUICK START

### Launch Sanskar (Any Environment)

```bash
# Development (local, isolated)
./run.sh --profile development

# Integration (with real TANTRA services)
./run.sh --profile integration

# Staging (high availability)
./run.sh --profile staging

# Production (locked-down, SLA-enforcing)
./run.sh --profile production
```

### Shutdown

```bash
./shutdown.sh
```

### Health Check

```bash
./health_check.sh
```

---

## CONFIGURATION ARCHITECTURE

### Directory Structure

```
runtime_config/
├── environment/
│   └── default.env                 # Base environment (NO local assumptions)
├── integration_profiles/
│   ├── development.env             # Dev isolated setup
│   ├── integration.env             # Integration with real services
│   ├── staging.env                 # Staging high-availability
│   └── production.env              # Production locked-down
└── deployment_profiles/
    ├── docker.conf                 # Docker containerized
    ├── kubernetes.conf             # Kubernetes orchestrated
    └── standalone.conf             # Bare-metal / VM
```

### Configuration Priority

1. **Command-line arguments** (highest)
2. **Profile-specific overrides** (integration_profiles/*.env)
3. **Deployment profile** (deployment_profiles/*.conf)
4. **Default environment** (default.env)
5. **Hardcoded defaults** (lowest)

### Example: Integration Profile Stacking

```bash
# Base environment
source runtime_config/environment/default.env

# Profile overrides
source runtime_config/integration_profiles/integration.env

# Deployment overrides
source runtime_config/deployment_profiles/docker.conf

# Command-line overrides
export SANSKAR_PORT=9001  # Override port from CLI
```

---

## ENVIRONMENT VARIABLES (NO HARDCODING)

All critical paths and endpoints are environment-driven:

```bash

RAJYA_DISCOVERY_URL=${RAJYA_SERVICE_URL:-http://rajya:8080}
ENFORCEMENT_DISCOVERY_URL=${ENFORCEMENT_SERVICE_URL:-http://enforcement:8080}
BUCKET_DISCOVERY_URL=${BUCKET_SERVICE_URL:-http://bucket:8080}
INSIGHTBRIDGE_DISCOVERY_URL=${INSIGHTBRIDGE_SERVICE_URL:-http://insightbridge:8080}


EVENT_STORE_URL=${EVENT_STORE_URL:-./event_store.db}
LINEAGE_PERSISTENCE_URL=${LINEAGE_PERSISTENCE_URL:-./lineage.json}


SANSKAR_PORT=${SANSKAR_PORT:-8001}
SANSKAR_HEALTH_PORT=${SANSKAR_HEALTH_PORT:-8002}
SANSKAR_METRICS_PORT=${SANSKAR_METRICS_PORT:-8003}


TRACE_EXPORT_BACKEND=${TRACE_EXPORT_BACKEND:-otlp}
```

---

## DEPLOYMENT PROFILES EXPLAINED

### Development

**When:** Local development, isolated testing  
**Characteristics:**
- Single-process simulation mode
- Debug endpoints enabled
- Local service discovery only
- Lenient timeouts (60s)
- No external dependencies required

**Launch:**
```bash
./run.sh --profile development
```

---

### Integration

**When:** Testing with real TANTRA services  
**Characteristics:**
- All TANTRA services required (rajya, enforcement, bucket, insightbridge)
- Strict governance enforcement
- Standard timeouts (30s)
- Full trace and replay validation
- Health checks all dependencies

**Launch:**
```bash
./run.sh --profile integration

```

**Requirements:**
```bash

export RAJYA_SERVICE_URL=http://rajya-service:8080
export ENFORCEMENT_SERVICE_URL=http://enforcement-service:8080
export BUCKET_SERVICE_URL=http://bucket-service:8080
export INSIGHTBRIDGE_SERVICE_URL=http://insightbridge-service:8080
```

---

### Staging

**When:** Pre-production validation with high availability  
**Characteristics:**
- Service discovery via Consul
- Multi-replica deployment
- Aggressive timeouts (15s)
- Circuit breaker enabled
- Redis caching
- High performance tuning

**Launch:**
```bash
./run.sh --profile staging

```

---

### Production

**When:** Live ecosystem deployment  
**Characteristics:**
- Kubernetes service discovery
- SLA-critical timeouts (10s)
- Audit logging to syslog
- Circuit breaker with exponential backoff
- Maximum concurrency (1000)
- Read-only root filesystem

**Launch:**
```bash
./run.sh --profile production

```

---

## DEPLOYMENT BACKENDS

### Docker

**For containerized deployments:**

```bash

docker build -t sanskar:latest -f Dockerfile.runtime .


docker run \
  --env-file runtime_config/integration_profiles/integration.env \
  -p 8001:8001 \
  -p 8002:8002 \
  -p 8003:8003 \
  sanskar:latest
```

**Health check in container:**
```bash
curl http://localhost:8002/health
```

---

### Kubernetes

**For orchestrated deployments:**

```bash

kubectl apply -f kubernetes/sanskar-deployment.yaml


kubectl get pods -l app=sanskar-participant


kubectl logs -f deployment/sanskar-participant


kubectl port-forward svc/sanskar-participant 8001:8001
```

**Configuration via ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sanskar-config
data:
  runtime.env: |
    $(cat runtime_config/integration_profiles/integration.env)
```

---

### Standalone

**For bare-metal or VM deployments:**

```bash

sudo cp runtime/sanskar-participant.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sanskar-participant
sudo systemctl start sanskar-participant


sudo systemctl status sanskar-participant


sudo journalctl -u sanskar-participant -f
```

---

## RUNTIME COMMANDS

### 1. Launch

```bash
./run.sh --profile ${PROFILE}
```

**Example outputs:**
```
[INFO] Loading environment: development
[INFO] Initializing contract registry
[INFO] Starting Sanskar participant on port 8001
[INFO] Health check endpoint: http://localhost:8002/health
[INFO] Ready for TANTRA ecosystem integration
```

---

### 2. Health Check

```bash
./health_check.sh
```

**Output:**
```
=== SANSKAR HEALTH CHECK ===

Runtime Status: HEALTHY
├─ Process ID: 12345
├─ Uptime: 3 hours 24 minutes
├─ Memory: 142 MB / 2 GB
└─ CPU: 0.2%

Service Connectivity:
├─ RAJYA: ✓ RESPONSIVE (25ms)
├─ Enforcement: ✓ RESPONSIVE (18ms)
├─ Bucket: ✓ RESPONSIVE (12ms)
└─ InsightBridge: ✓ RESPONSIVE (35ms)

Governance Status:
├─ Constitutional Boundaries: ✓ ACTIVE
├─ Trace Immutability: ✓ ENABLED
└─ Replay Verification: ✓ ENABLED

Readiness: ✓ READY FOR OPERATION
Liveness: ✓ HEALTHY
```

---

### 3. Shutdown

```bash
./shutdown.sh
```

**Graceful shutdown (30 second timeout):**
```
[INFO] Shutting down Sanskar participant
[INFO] Flushing pending traces
[INFO] Persisting lineage data
[INFO] Closing database connections
[INFO] Graceful shutdown complete
```

---

## TRACE CONTINUITY ACROSS DEPLOYMENTS

No matter the deployment profile or backend, trace_id is **immutable**:

```bash

Request: TRACE-abc123def456
Sanskar: TRACE-abc123def456
Storage: TRACE-abc123def456


Request: TRACE-abc123def456
Sanskar: TRACE-abc123def456
RAJYA: TRACE-abc123def456
Enforcement: TRACE-abc123def456
Bucket: TRACE-abc123def456
InsightBridge: TRACE-abc123def456


Pod 1/3: TRACE-abc123def456
Pod 2/3: TRACE-abc123def456
Pod 3/3: TRACE-abc123def456
```

---

## PORTABLE CONFIGURATION EXAMPLES

### Example 1: Deploy to New Kubernetes Cluster

**No code changes required:**

```bash

export RAJYA_SERVICE_URL=http://rajya-prod-cluster.company.com:8080
export ENFORCEMENT_SERVICE_URL=http://enforcement-prod-cluster.company.com:8080
export BUCKET_SERVICE_URL=http://bucket-prod-cluster.company.com:8080
export INSIGHTBRIDGE_SERVICE_URL=http://insightbridge-prod-cluster.company.com:8080


./run.sh --profile production
```

---

### Example 2: Development on Laptop

**Single-process, no external dependencies:**

```bash

./run.sh --profile development


```

---

### Example 3: CI/CD Pipeline

**Consistent deployment across environments:**

```bash


docker build -t sanskar:${BUILD_NUMBER} .


docker run \
  --env-file runtime_config/integration_profiles/development.env \
  sanskar:${BUILD_NUMBER} \
  python -m pytest tests/


docker push sanskar:${BUILD_NUMBER}
kubectl set image deployment/sanskar-staging \
  sanskar=sanskar:${BUILD_NUMBER}


kubectl set image deployment/sanskar-prod \
  sanskar=sanskar:${BUILD_NUMBER}
```

---

## NO HARDCODED ASSUMPTIONS

### What's NOT Hardcoded

-  Service URLs (all environment-driven)
-  Port numbers (configurable per deployment)
-  Storage paths (can be local, S3, database)
-  Timeouts (profile-specific)
-  Log levels (configurable)
-  Memory limits (deployment-specific)

### What IS Portable

-  Contract schema definitions
-  Governance boundaries
-  Trace immutability logic
-  Replay determinism
-  Error handling
-  Integration procedures

---

## NEXT STEPS

1. **Choose deployment profile** (development/integration/staging/production)
2. **Set environment variables** from profile
3. **Run launch command** (`./run.sh --profile <profile>`)
4. **Verify health check** (`./health_check.sh`)
5. **Proceed to Phase 2** (Canonical TANTRA Adapter Layer)

---

**Status:**  Phase 1 Complete - Plug-and-Play Runtime Package Ready  
**Next:** Phase 2 - Canonical TANTRA Adapter Layer
