#!/bin/bash

################################################################################
# SANSKAR PLUG-AND-PLAY RUNTIME - SHUTDOWN
################################################################################
#
# Graceful shutdown of SANSKAR participant with cleanup
#
# Features:
#   - Graceful termination (30 second timeout)
#   - Flush pending traces
#   - Persist lineage data
#   - Close database connections
#   - Clean up resources
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
GRACEFUL_TIMEOUT=30

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

################################################################################
# CHECK IF PROCESS IS RUNNING
################################################################################

log_info "Shutting down SANSKAR participant..."

if [ ! -f "$PIDFILE" ]; then
    log_warning "PID file not found: $PIDFILE"
    log_info "SANSKAR may not be running"
    exit 0
fi

SANSKAR_PID=$(cat "$PIDFILE")

if ! kill -0 $SANSKAR_PID 2>/dev/null; then
    log_warning "Process $SANSKAR_PID is not running"
    rm -f "$PIDFILE"
    exit 0
fi

log_info "Found SANSKAR process: $SANSKAR_PID"

################################################################################
# GRACEFUL SHUTDOWN
################################################################################

log_info "Initiating graceful shutdown (${GRACEFUL_TIMEOUT}s timeout)..."


kill -TERM $SANSKAR_PID 2>/dev/null || true

WAIT_TIME=0
while [ $WAIT_TIME -lt $GRACEFUL_TIMEOUT ]; do
    if ! kill -0 $SANSKAR_PID 2>/dev/null; then
        log_success "SANSKAR gracefully terminated"
        rm -f "$PIDFILE"
        exit 0
    fi
    
    sleep 1
    WAIT_TIME=$((WAIT_TIME + 1))
    
    if [ $((WAIT_TIME % 5)) -eq 0 ]; then
        echo -ne "\rWaiting for graceful shutdown... ${WAIT_TIME}s"
    fi
done

echo ""

################################################################################
# FORCE KILL IF NECESSARY
################################################################################

log_warning "Graceful shutdown timeout exceeded, forcing termination..."

kill -9 $SANSKAR_PID 2>/dev/null || true
sleep 1

if kill -0 $SANSKAR_PID 2>/dev/null; then
    log_error "Failed to terminate SANSKAR process"
    exit 1
fi

log_success "SANSKAR process terminated"
rm -f "$PIDFILE"

################################################################################
# CLEANUP
################################################################################

log_info "Cleaning up resources..."


find "$SCRIPT_DIR/.runtime" -type f -name "*.lock" -delete 2>/dev/null || true


if [ -d "$SCRIPT_DIR/logs" ]; then
    ARCHIVE_DIR="$SCRIPT_DIR/logs/archives"
    mkdir -p "$ARCHIVE_DIR"
    
    
    find "$SCRIPT_DIR/logs" -maxdepth 1 -name "sanskar_*.log" -mtime +7 -exec mv {} "$ARCHIVE_DIR" \; 2>/dev/null || true
    
    log_info "Archived old logs to $ARCHIVE_DIR"
fi

################################################################################
# FINAL STATUS
################################################################################

log_success "SANSKAR participant shutdown complete"
log_info ""
log_info "Shutdown Summary:"
log_info "  Process: Terminated"
log_info "  Resources: Cleaned"
log_info "  Status: OFFLINE"
log_info ""
log_info "To restart:"
log_info "  ./run.sh --profile <profile>"
log_info ""
