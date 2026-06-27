#!/bin/bash
# Health check script for Telegram Calendar Bot

set -e

# Configuration
PID_FILE="/app/data/bot.pid"
LOG_FILE="/app/logs/bot.log"
MAX_LOG_AGE=300  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Check if bot process is running
check_process() {
    if [ ! -f "$PID_FILE" ]; then
        error "PID file not found: $PID_FILE"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE" 2>/dev/null)
    if [ -z "$pid" ]; then
        error "Empty PID file"
        return 1
    fi
    
    if ! kill -0 "$pid" 2>/dev/null; then
        error "Process $pid is not running"
        return 1
    fi
    
    log "Bot process $pid is running"
    return 0
}

# Check log file for recent activity
check_log_activity() {
    if [ ! -f "$LOG_FILE" ]; then
        warn "Log file not found: $LOG_FILE"
        return 0  # Not critical for health check
    fi
    
    local log_age=$(stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0)
    local current_time=$(date +%s)
    local age_diff=$((current_time - log_age))
    
    if [ $age_diff -gt $MAX_LOG_AGE ]; then
        warn "Log file is older than ${MAX_LOG_AGE}s (${age_diff}s old)"
        return 0  # Warning, not error
    fi
    
    log "Log file is active (last modified ${age_diff}s ago)"
    return 0
}

# Check memory usage
check_memory() {
    if [ ! -f "$PID_FILE" ]; then
        return 1
    fi
    
    local pid=$(cat "$PID_FILE" 2>/dev/null)
    if [ -z "$pid" ]; then
        return 1
    fi
    
    # Get memory usage in MB
    local memory_kb=$(ps -o rss= -p "$pid" 2>/dev/null || echo 0)
    local memory_mb=$((memory_kb / 1024))
    
    if [ $memory_mb -gt 400 ]; then  # 400MB threshold
        warn "High memory usage: ${memory_mb}MB"
        return 0  # Warning, not error
    fi
    
    log "Memory usage: ${memory_mb}MB"
    return 0
}

# Check disk space
check_disk_space() {
    local available=$(df /app | awk 'NR==2 {print $4}')
    local available_mb=$((available / 1024))
    
    if [ $available_mb -lt 100 ]; then  # 100MB threshold
        error "Low disk space: ${available_mb}MB available"
        return 1
    fi
    
    log "Disk space: ${available_mb}MB available"
    return 0
}

# Check environment variables
check_environment() {
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        error "TELEGRAM_BOT_TOKEN not set"
        return 1
    fi
    
    local token_length=${#TELEGRAM_BOT_TOKEN}
    if [ $token_length -lt 35 ]; then  # Telegram tokens are ~45 chars
        error "TELEGRAM_BOT_TOKEN appears invalid (too short)"
        return 1
    fi
    
    log "Environment variables OK"
    return 0
}

# Main health check
main() {
    log "Starting health check..."
    
    local exit_code=0
    
    # Run all checks
    check_environment || exit_code=1
    check_process || exit_code=1
    check_disk_space || exit_code=1
    check_memory || exit_code=0  # Memory is warning only
    check_log_activity || exit_code=0  # Log activity is warning only
    
    if [ $exit_code -eq 0 ]; then
        log "Health check passed ✅"
    else
        error "Health check failed ❌"
    fi
    
    return $exit_code
}

# Run health check
main "$@"