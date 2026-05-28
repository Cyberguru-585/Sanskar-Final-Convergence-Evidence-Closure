#!/bin/bash

################################################################################
# SANSKAR PLUG-AND-PLAY RUNTIME - HEALTH CHECK
################################################################################
#
# Comprehensive health verification of SANSKAR and downstream ecosystem
#
# Features:
#   - SANSKAR process status
#   - Memory and CPU usage
#   - Service connectivity checks
#   - Governance status
#   - Trace immutability verification
#   - Replay capability check
#   - Overall readiness assessment
#
################################################################################

set -e


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' 


SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PIDFILE="$SCRIPT_DIR/.runtime/sanskar.pid"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Load configuration
if [ -f "$SCRIPT_DIR/runtime_config/environment/default.env" ]; then
    set -a
    source "$SCRIPT_DIR/runtime_config/environment/default.env"
    set +a
fi

################################################################################
# HEADER
################################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          SANSKAR ECOSYSTEM HEALTH CHECK                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

HEALTHY=true
CHECKS_PASSED=0
CHECKS_FAILED=0

################################################################################
# 1. SANSKAR PROCESS STATUS
################################################################################

echo -e "${BLUE}═══ SANSKAR PROCESS STATUS ═══${NC}"
echo ""

if [ ! -f "$PIDFILE" ]; then
    log_error "PID file not found: SANSKAR not started"
    echo "  → Run: ./run.sh --profile <profile>"
    HEALTHY=false
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
else
    SANSKAR_PID=$(cat "$PIDFILE")
    
    if kill -0 $SANSKAR_PID 2>/dev/null; then
        log_success "Process running (PID: $SANSKAR_PID)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        
        
        UPTIME_SECONDS=$(ps -o etime= -p $SANSKAR_PID | tr -d ' ' | awk -F: '{print ($NF) + ($NF-1)*60 + ($NF-2)*3600}')
        UPTIME_READABLE=$(printf '%dh %dm %ds' $((UPTIME_SECONDS/3600)) $((UPTIME_SECONDS%3600/60)) $((UPTIME_SECONDS%60)))
        log_info "Uptime: $UPTIME_READABLE"
        
        
        if command -v ps &> /dev/null; then
            MEMORY=$(ps -o rss= -p $SANSKAR_PID 2>/dev/null || echo "0")
            MEMORY_MB=$((MEMORY / 1024))
            log_info "Memory: ~${MEMORY_MB} MB"
        fi
        
        
        if command -v ps &> /dev/null; then
            CPU=$(ps -o %cpu= -p $SANSKAR_PID 2>/dev/null || echo "0")
            log_info "CPU: ${CPU}%"
        fi
    else
        log_error "Process not running (stale PID: $SANSKAR_PID)"
        log_warning "PID file exists but process is dead. Run: ./run.sh --profile <profile>"
        rm -f "$PIDFILE"
        HEALTHY=false
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
fi

echo ""

################################################################################
# 2. PORT AVAILABILITY
################################################################################

echo -e "${BLUE}═══ PORT AVAILABILITY ═══${NC}"
echo ""


if [ ! -z "$SANSKAR_PORT" ]; then
    if curl -s "http://localhost:$SANSKAR_PORT" > /dev/null 2>&1; then
        log_success "Main API port $SANSKAR_PORT is responding"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_warning "Main API port $SANSKAR_PORT not responding"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    log_error "SANSKAR_PORT not configured"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi


if [ ! -z "$SANSKAR_HEALTH_PORT" ]; then
    if curl -s "http://localhost:$SANSKAR_HEALTH_PORT/health" > /dev/null 2>&1; then
        log_success "Health check port $SANSKAR_HEALTH_PORT is responding"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_warning "Health check port $SANSKAR_HEALTH_PORT not responding"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    log_error "SANSKAR_HEALTH_PORT not configured"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi


if [ ! -z "$SANSKAR_METRICS_PORT" ]; then
    if curl -s "http://localhost:$SANSKAR_METRICS_PORT/metrics" > /dev/null 2>&1; then
        log_success "Metrics port $SANSKAR_METRICS_PORT is responding"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_warning "Metrics port $SANSKAR_METRICS_PORT not responding"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    log_error "SANSKAR_METRICS_PORT not configured"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

echo ""

################################################################################
# 3. SERVICE CONNECTIVITY
################################################################################

echo -e "${BLUE}═══ SERVICE CONNECTIVITY ═══${NC}"
echo ""

check_service() {
    local SERVICE_NAME=$1
    local SERVICE_URL=$2
    
    if [ -z "$SERVICE_URL" ]; then
        log_error "$SERVICE_NAME: URL not configured"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
    
    
    if timeout 5 curl -s "$SERVICE_URL/health" > /dev/null 2>&1; then
        LATENCY=$(curl -w "%{time_total}\n" -o /dev/null -s "$SERVICE_URL/health")
        log_success "$SERVICE_NAME: ✓ RESPONSIVE (${LATENCY}s)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        log_warning "$SERVICE_NAME: UNRESPONSIVE ($SERVICE_URL)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
}

check_service "RAJYA" "${RAJYA_SERVICE_URL}"
check_service "Enforcement" "${ENFORCEMENT_SERVICE_URL}"
check_service "Bucket" "${BUCKET_SERVICE_URL}"
check_service "InsightBridge" "${INSIGHTBRIDGE_SERVICE_URL}"

echo ""

################################################################################
# 4. GOVERNANCE STATUS
################################################################################

echo -e "${BLUE}═══ GOVERNANCE STATUS ═══${NC}"
echo ""


if [ -f "$SCRIPT_DIR/governance_drift_check.json" ]; then
    DRIFT=$(grep -o '"governance_drift":[^,}]*' "$SCRIPT_DIR/governance_drift_check.json" | tail -1 | awk -F: '{print $2}')
    if [ "$DRIFT" = "0.0" ] || [ "$DRIFT" = "0" ]; then
        log_success "Constitutional Boundaries: ✓ ACTIVE"
        log_info "Governance drift: 0.0"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_warning "Constitutional Boundaries: DRIFT DETECTED ($DRIFT)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    log_info "Governance status: Not yet initialized"
fi


if [ -f "$SCRIPT_DIR/trace_continuity_proof.json" ]; then
    TRACE_PRESERVED=$(grep -o '"trace_preserved":true' "$SCRIPT_DIR/trace_continuity_proof.json" | wc -l)
    if [ $TRACE_PRESERVED -gt 0 ]; then
        log_success "Trace Immutability: ✓ ENABLED"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_error "Trace Immutability: ✗ VIOLATIONS DETECTED"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
fi


if [ -f "$SCRIPT_DIR/replay_boundary_validation.json" ]; then
    DETERMINISM=$(grep -o '"determinism":1.0\|"determinism":100' "$SCRIPT_DIR/replay_boundary_validation.json" | wc -l)
    if [ $DETERMINISM -gt 0 ]; then
        log_success "Replay Verification: ✓ ENABLED"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_warning "Replay Verification: Not verified"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
fi

echo ""

################################################################################
# 5. STORAGE & PERSISTENCE
################################################################################

echo -e "${BLUE}═══ STORAGE & PERSISTENCE ═══${NC}"
echo ""


if [ -f "$SCRIPT_DIR/event_store.json" ]; then
    SIZE=$(du -h "$SCRIPT_DIR/event_store.json" | awk '{print $1}')
    EVENTS=$(grep -o '"type"' "$SCRIPT_DIR/event_store.json" | wc -l)
    log_success "Event Store: $SIZE ($EVENTS events)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    log_info "Event Store: Not yet created"
fi


if [ -f "$SCRIPT_DIR/lineage.json" ]; then
    SIZE=$(du -h "$SCRIPT_DIR/lineage.json" | awk '{print $1}')
    log_success "Lineage Persistence: $SIZE"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    log_info "Lineage Persistence: Not yet created"
fi

echo ""

################################################################################
# 6. OBSERVABILITY
################################################################################

echo -e "${BLUE}═══ OBSERVABILITY ═══${NC}"
echo ""


if [ -f "$SCRIPT_DIR/observability.log" ]; then
    LINES=$(wc -l < "$SCRIPT_DIR/observability.log")
    SIZE=$(du -h "$SCRIPT_DIR/observability.log" | awk '{print $1}')
    log_success "Observability Log: $SIZE ($LINES lines)"
    
    
    ERRORS=$(grep -c "ERROR\|FAILED" "$SCRIPT_DIR/observability.log" 2>/dev/null || echo "0")
    if [ "$ERRORS" = "0" ]; then
        log_success "No recent errors in logs"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_warning "Recent errors in logs: $ERRORS"
        tail -3 "$SCRIPT_DIR/observability.log" | sed 's/^/    /'
    fi
else
    log_info "Observability Log: Not yet created"
fi

echo ""

################################################################################
# 7. READINESS & LIVENESS
################################################################################

echo -e "${BLUE}═══ READINESS & LIVENESS ═══${NC}"
echo ""


if [ "$HEALTHY" = true ] && [ "$CHECKS_FAILED" -lt 3 ]; then
    log_success "Readiness: ✓ READY FOR OPERATION"
    READINESS="READY"
else
    log_error "Readiness: ✗ NOT READY (fix issues above)"
    READINESS="NOT_READY"
fi


if [ -f "$PIDFILE" ]; then
    SANSKAR_PID=$(cat "$PIDFILE")
    if kill -0 $SANSKAR_PID 2>/dev/null; then
        log_success "Liveness: ✓ HEALTHY"
        LIVENESS="HEALTHY"
    else
        log_error "Liveness: ✗ DEAD"
        LIVENESS="DEAD"
        HEALTHY=false
    fi
else
    log_error "Liveness: ✗ NOT RUNNING"
    LIVENESS="NOT_RUNNING"
    HEALTHY=false
fi

echo ""

################################################################################
# SUMMARY
################################################################################

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    HEALTH CHECK SUMMARY                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "  Checks Passed: $CHECKS_PASSED"
echo "  Checks Failed: $CHECKS_FAILED"
echo ""
echo "  Readiness: $READINESS"
echo "  Liveness: $LIVENESS"
echo ""

if [ "$HEALTHY" = true ]; then
    echo -e "${GREEN}━━ SYSTEM HEALTHY ━━${NC}"
    echo ""
    echo "SANSKAR is ready for operation. You can:"
    echo "  - Run integration tests: python tantra_integration_harness.py"
    echo "  - Check boundaries: python constitutional_pressure_tests.py"
    echo "  - Monitor: tail -f observability.log"
    echo ""
    exit 0
else
    echo -e "${RED}━━ SYSTEM ISSUES DETECTED ━━${NC}"
    echo ""
    echo "Please fix the issues above and retry."
    echo "For debugging, check:"
    echo "  - Logs: ls -la logs/"
    echo "  - Environment: echo \$RAJYA_SERVICE_URL"
    echo "  - Manual test: curl http://localhost:$SANSKAR_PORT"
    echo ""
    exit 1
fi
