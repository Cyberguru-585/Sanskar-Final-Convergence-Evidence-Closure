#!/bin/bash

################################################################################
# SANSKAR PLUG-AND-PLAY RUNTIME - LAUNCHER
################################################################################
#
# Universal launcher for SANSKAR participant in any deployment profile
#
# Usage:
#   ./run.sh --profile development
#   ./run.sh --profile integration
#   ./run.sh --profile staging
#   ./run.sh --profile production
#
# Features:
#   - Environment-driven configuration (zero hardcoding)
#   - Multi-profile support
#   - Deterministic contract exchange
#   - Immutable trace_id propagation
#   - Production-grade observability
#
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' 


SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROFILE="${PROFILE:-development}"
VERBOSE=false
PROFILE_FILE=""


while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE    Deployment profile (development/integration/staging/production)"
            echo "  --verbose            Enable verbose logging"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run.sh --profile development"
            echo "  ./run.sh --profile integration --verbose"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

################################################################################
# LOAD CONFIGURATION
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load base environment
if [ -f "$SCRIPT_DIR/runtime_config/environment/default.env" ]; then
    log_info "Loading default environment..."
    set -a
    source "$SCRIPT_DIR/runtime_config/environment/default.env"
    set +a
else
    log_error "Default environment not found: runtime_config/environment/default.env"
    exit 1
fi


PROFILE_FILE="$SCRIPT_DIR/runtime_config/integration_profiles/${PROFILE}.env"
if [ -f "$PROFILE_FILE" ]; then
    log_info "Loading profile: ${PROFILE}"
    set -a
    source "$PROFILE_FILE"
    set +a
else
    log_error "Profile not found: ${PROFILE}"
    log_info "Available profiles:"
    ls "$SCRIPT_DIR/runtime_config/integration_profiles/" | sed 's/\.env$//'
    exit 1
fi


if [ -f "$SCRIPT_DIR/runtime_config/deployment_profiles/${DEPLOYMENT_BACKEND:-standalone}.conf" ]; then
    log_info "Loading deployment profile: ${DEPLOYMENT_BACKEND:-standalone}"
    set -a
    source "$SCRIPT_DIR/runtime_config/deployment_profiles/${DEPLOYMENT_BACKEND:-standalone}.conf"
    set +a
fi

################################################################################
# VALIDATE CONFIGURATION
################################################################################

log_info "Validating configuration..."


REQUIRED_VARS=(
    "SANSKAR_PORT"
    "SANSKAR_HEALTH_PORT"
    "SANSKAR_METRICS_PORT"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable not set: $var"
        exit 1
    fi
done

if [ "$VERBOSE" = true ]; then
    log_info "Configuration:"
    log_info "  Profile: $PROFILE"
    log_info "  Sanskar Port: $SANSKAR_PORT"
    log_info "  Health Port: $SANSKAR_HEALTH_PORT"
    log_info "  Metrics Port: $SANSKAR_METRICS_PORT"
    log_info "  RAJYA URL: ${RAJYA_SERVICE_URL}"
    log_info "  Enforcement URL: ${ENFORCEMENT_SERVICE_URL}"
    log_info "  Bucket URL: ${BUCKET_SERVICE_URL}"
    log_info "  InsightBridge URL: ${INSIGHTBRIDGE_SERVICE_URL}"
fi

################################################################################
# PRE-FLIGHT CHECKS
################################################################################

log_info "Running pre-flight checks..."


if lsof -Pi :$SANSKAR_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    log_error "Port $SANSKAR_PORT is already in use"
    exit 1
fi


if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi


PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_info "Python version: $PYTHON_VERSION"

################################################################################
# INITIALIZE RUNTIME ENVIRONMENT
################################################################################

log_info "Initializing runtime environment..."

mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/.runtime"


echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$SCRIPT_DIR/.runtime/startup_time"


PIDFILE="$SCRIPT_DIR/.runtime/sanskar.pid"

################################################################################
# START SANSKAR PARTICIPANT
################################################################################

log_info "Starting SANSKAR participant ($PROFILE profile)..."


PYTHON_CMD="python3"


LOGFILE="$SCRIPT_DIR/logs/sanskar_${PROFILE}_$(date +%Y%m%d_%H%M%S).log"

$PYTHON_CMD "$SCRIPT_DIR/sanskar.py" \
    --profile "$PROFILE" \
    --port "$SANSKAR_PORT" \
    --health-port "$SANSKAR_HEALTH_PORT" \
    --metrics-port "$SANSKAR_METRICS_PORT" \
    > "$LOGFILE" 2>&1 &

SANSKAR_PID=$!
echo $SANSKAR_PID > "$PIDFILE"

log_info "SANSKAR PID: $SANSKAR_PID"
log_info "Log file: $LOGFILE"

################################################################################
# WAIT FOR STARTUP
################################################################################

log_info "Waiting for SANSKAR to become ready..."

MAX_WAIT=30
WAIT_TIME=0
INTERVAL=1

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if curl -s "http://localhost:$SANSKAR_HEALTH_PORT/health" > /dev/null 2>&1; then
        log_success "SANSKAR health check passed"
        break
    fi
    
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
    echo -ne "\rWaiting for startup... ${WAIT_TIME}s"
done

echo ""

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    log_error "SANSKAR failed to start within ${MAX_WAIT}s"
    log_error "Check logs: $LOGFILE"
    kill $SANSKAR_PID 2>/dev/null || true
    exit 1
fi

################################################################################
# INITIALIZATION COMPLETE
################################################################################

log_success "SANSKAR participant is ready"
log_info ""
log_info "Runtime Status:"
log_info "  Process ID: $SANSKAR_PID"
log_info "  Status: READY"
log_info "  Main API: http://localhost:$SANSKAR_PORT"
log_info "  Health Check: http://localhost:$SANSKAR_HEALTH_PORT/health"
log_info "  Metrics: http://localhost:$SANSKAR_METRICS_PORT/metrics"
log_info ""
log_info "Downstream Participants:"
log_info "  RAJYA: ${RAJYA_SERVICE_URL}"
log_info "  Enforcement: ${ENFORCEMENT_SERVICE_URL}"
log_info "  Bucket: ${BUCKET_SERVICE_URL}"
log_info "  InsightBridge: ${INSIGHTBRIDGE_SERVICE_URL}"
log_info ""
log_info "To verify health:"
log_info "  ./health_check.sh"
log_info ""
log_info "To shutdown:"
log_info "  ./shutdown.sh"
log_info ""

################################################################################
# KEEP PROCESS ALIVE
################################################################################


wait $SANSKAR_PID


log_warning "SANSKAR process exited with code: $?"
rm -f "$PIDFILE"
exit 1
