#!/bin/bash
# Deployment script for Telegram Calendar Bot

set -e

# Configuration
PROJECT_NAME="telegram-calendar-bot"
IMAGE_NAME="telegram-calendar-bot"
CONTAINER_NAME="telegram-calendar-bot"
NETWORK_NAME="bot-network"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO:${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
    log "Docker is running"
}

# Check if docker-compose is available
check_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "docker-compose not found"
        exit 1
    fi
    log "docker-compose is available"
}

# Validate environment file
validate_env() {
    if [ ! -f ".env" ]; then
        warn ".env file not found"
        info "Creating template .env file..."
        cat > .env << EOF
# Telegram Calendar Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_CALENDAR_ID=
GOOGLE_CREDENTIALS_FILE=/app/credentials.json
RATE_LIMIT_PER_MINUTE=20
LOG_LEVEL=INFO
EOF
        warn "Please edit .env file with your actual configuration"
        return 1
    fi
    
    # Check required variables
    if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here" .env; then
        error "TELEGRAM_BOT_TOKEN not configured in .env"
        return 1
    fi
    
    log "Environment configuration validated"
    return 0
}

# Create necessary directories
setup_directories() {
    log "Setting up directories..."
    mkdir -p data logs
    chmod 755 data logs
    log "Directories created"
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    docker build -t "$IMAGE_NAME:latest" .
    
    if [ $? -eq 0 ]; then
        log "Docker image built successfully"
    else
        error "Failed to build Docker image"
        exit 1
    fi
}

# Stop existing container
stop_existing() {
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        log "Stopping existing container..."
        docker-compose down
        log "Container stopped"
    else
        info "No existing container found"
    fi
}

# Start the bot
start_bot() {
    log "Starting bot with docker-compose..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log "Bot started successfully"
        
        # Wait a bit and check health
        sleep 5
        if docker ps -q -f name="$CONTAINER_NAME" -f status=running | grep -q .; then
            log "✅ Bot is running and healthy"
            show_status
        else
            error "❌ Bot failed to start properly"
            show_logs
            exit 1
        fi
    else
        error "Failed to start bot"
        exit 1
    fi
}

# Show container status
show_status() {
    echo ""
    info "=== Container Status ==="
    docker ps -f name="$CONTAINER_NAME"
    
    echo ""
    info "=== Resource Usage ==="
    docker stats "$CONTAINER_NAME" --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Show recent logs
show_logs() {
    echo ""
    info "=== Recent Logs ==="
    docker-compose logs --tail=20 "$PROJECT_NAME"
}

# Deployment modes
deploy_development() {
    log "🚀 Deploying in DEVELOPMENT mode"
    
    check_docker
    check_compose
    validate_env || exit 1
    setup_directories
    stop_existing
    build_image
    start_bot
    
    echo ""
    log "✅ Development deployment complete!"
    info "Use 'docker-compose logs -f' to follow logs"
    info "Use 'docker-compose down' to stop"
}

deploy_production() {
    log "🚀 Deploying in PRODUCTION mode"
    
    check_docker
    check_compose
    validate_env || exit 1
    setup_directories
    
    # Production-specific validations
    if [ ! -f "credentials.json" ]; then
        warn "credentials.json not found - Google Calendar integration will not work"
    fi
    
    # Backup existing data
    if [ -d "data" ] && [ "$(ls -A data)" ]; then
        log "Creating backup of existing data..."
        ./scripts/backup.sh
    fi
    
    stop_existing
    build_image
    start_bot
    
    # Setup log rotation for production
    setup_log_rotation
    
    echo ""
    log "✅ Production deployment complete!"
    info "Bot is running in production mode"
    info "Logs: docker-compose logs -f"
    info "Stop: docker-compose down"
    info "Health: ./scripts/healthcheck.sh"
}

# Setup log rotation (production only)
setup_log_rotation() {
    if command -v logrotate >/dev/null 2>&1; then
        log "Setting up log rotation..."
        cat > /etc/logrotate.d/telegram-calendar-bot << EOF
/opt/data/profiles/coder/home/projects/telegram-calendar-bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 1000 1000
    postrotate
        docker-compose restart telegram-calendar-bot
    endscript
}
EOF
        info "Log rotation configured"
    else
        warn "logrotate not available - manual log management required"
    fi
}

# Update existing deployment
update() {
    log "🔄 Updating existing deployment"
    
    check_docker
    check_compose
    
    # Pull latest code (if using git)
    if [ -d ".git" ]; then
        log "Pulling latest code..."
        git pull
    fi
    
    # Build new image
    build_image
    
    # Rolling update
    log "Performing rolling update..."
    docker-compose up -d --no-deps "$PROJECT_NAME"
    
    log "✅ Update complete"
}

# Rollback to previous version
rollback() {
    warn "🔄 Rolling back to previous version"
    
    # Find previous image
    PREVIOUS_IMAGE=$(docker images "$IMAGE_NAME" --format "{{.ID}}" | sed -n '2p')
    
    if [ -z "$PREVIOUS_IMAGE" ]; then
        error "No previous image found for rollback"
        exit 1
    fi
    
    log "Rolling back to image: $PREVIOUS_IMAGE"
    
    # Tag previous image as latest
    docker tag "$PREVIOUS_IMAGE" "$IMAGE_NAME:latest"
    
    # Restart with previous image
    docker-compose down
    docker-compose up -d
    
    log "✅ Rollback complete"
}

# Health check
health_check() {
    log "🏥 Running health check..."
    
    if [ -f "scripts/healthcheck.sh" ]; then
        ./scripts/healthcheck.sh
    else
        # Basic health check
        if docker ps -q -f name="$CONTAINER_NAME" -f status=running | grep -q .; then
            log "✅ Container is running"
        else
            error "❌ Container is not running"
            exit 1
        fi
    fi
}

# Print usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Deploy in development mode"
    echo "  prod        Deploy in production mode (with backups and log rotation)"
    echo "  update      Update existing deployment"
    echo "  rollback    Rollback to previous version"
    echo "  health      Run health check"
    echo "  status      Show container status"
    echo "  logs        Show recent logs"
    echo "  stop        Stop the bot"
    echo "  clean       Stop and remove containers, networks, images"
    echo ""
    echo "Examples:"
    echo "  $0 dev          # Quick development deployment"
    echo "  $0 prod         # Production deployment with all safeguards"
    echo "  $0 update       # Update to latest version"
    echo "  $0 logs         # Show recent logs"
}

# Main command handling
case "${1:-}" in
    "dev"|"development")
        deploy_development
        ;;
    "prod"|"production")
        deploy_production
        ;;
    "update")
        update
        ;;
    "rollback")
        rollback
        ;;
    "health")
        health_check
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        log "Stopping bot..."
        docker-compose down
        log "✅ Bot stopped"
        ;;
    "clean")
        warn "⚠️ This will remove all containers, networks, and images"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi all
            docker system prune -f
            log "✅ Cleanup complete"
        else
            info "Cleanup cancelled"
        fi
        ;;
    "help"|"--help"|"-h"|"")
        usage
        ;;
    *)
        error "Unknown command: $1"
        usage
        exit 1
        ;;
esac