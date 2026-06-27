#!/bin/bash
# Backup script for Telegram Calendar Bot

set -e

# Configuration
BACKUP_DIR="backups"
PROJECT_DIR="/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="telegram-bot-backup-$TIMESTAMP"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Create backup directory
setup_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log "Backup directory ready: $BACKUP_DIR"
}

# Backup application data
backup_data() {
    log "Backing up application data..."
    
    local backup_file="$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    
    # Create list of files/directories to backup
    local backup_items=""
    
    # Data directory (bot state, cache, etc.)
    if [ -d "data" ]; then
        backup_items="$backup_items data"
        log "Including data directory"
    fi
    
    # Configuration files
    if [ -f ".env" ]; then
        backup_items="$backup_items .env"
        log "Including .env configuration"
    fi
    
    if [ -f "config.json" ]; then
        backup_items="$backup_items config.json"
        log "Including config.json"
    fi
    
    # Google credentials (if present)
    if [ -f "credentials.json" ]; then
        backup_items="$backup_items credentials.json"
        log "Including Google credentials"
    fi
    
    # Recent logs (last 7 days)
    if [ -d "logs" ]; then
        log "Including recent logs..."
        find logs -name "*.log" -mtime -7 -exec tar -rf "$backup_file.tmp" {} \; 2>/dev/null || true
    fi
    
    if [ -n "$backup_items" ]; then
        tar -czf "$backup_file" $backup_items
        log "✅ Backup created: $backup_file"
        
        # Show backup size
        local size=$(du -h "$backup_file" | cut -f1)
        log "Backup size: $size"
        
        return 0
    else
        warn "No data found to backup"
        return 1
    fi
}

# Backup Docker volumes (if running in container)
backup_volumes() {
    log "Checking for Docker volumes..."
    
    local container_name="telegram-calendar-bot"
    
    if docker ps -q -f name="$container_name" | grep -q .; then
        log "Backing up Docker container data..."
        
        local volume_backup="$BACKUP_DIR/${BACKUP_NAME}-volumes.tar.gz"
        
        # Backup container volumes
        docker run --rm \
            --volumes-from "$container_name" \
            -v "$(pwd)/$BACKUP_DIR:/backup" \
            alpine \
            tar czf "/backup/$(basename $volume_backup)" /app/data /app/logs 2>/dev/null || true
            
        if [ -f "$volume_backup" ]; then
            log "✅ Volume backup created: $volume_backup"
        else
            warn "Volume backup failed or no volumes found"
        fi
    else
        log "No running container found, skipping volume backup"
    fi
}

# Export database (if using database)
backup_database() {
    log "Checking for database..."
    
    # Check if we have database configuration
    if [ -f ".env" ]; then
        source .env
        
        if [ -n "${DATABASE_URL:-}" ]; then
            log "Backing up database..."
            
            local db_backup="$BACKUP_DIR/${BACKUP_NAME}-database.sql"
            
            # Export database (example for PostgreSQL)
            if [[ "$DATABASE_URL" == *"postgresql"* ]]; then
                pg_dump "$DATABASE_URL" > "$db_backup" 2>/dev/null || {
                    warn "Database backup failed"
                    return 1
                }
                log "✅ Database backup created: $db_backup"
            fi
        else
            log "No database configured, skipping database backup"
        fi
    fi
}

# Create backup manifest
create_manifest() {
    local manifest_file="$BACKUP_DIR/${BACKUP_NAME}-manifest.json"
    
    log "Creating backup manifest..."
    
    cat > "$manifest_file" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "project_dir": "$(pwd)",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'not-a-git-repo')",
    "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
    "files": [
        $(find "$BACKUP_DIR" -name "${BACKUP_NAME}*" -type f -printf '"%f",\n' | sed '$ s/,$//')
    ],
    "size_bytes": $(find "$BACKUP_DIR" -name "${BACKUP_NAME}*" -type f -exec du -bc {} + | tail -1 | cut -f1),
    "restore_instructions": "Use ./scripts/restore.sh with this backup manifest"
}
EOF
    
    log "✅ Manifest created: $manifest_file"
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    if [ -d "$BACKUP_DIR" ]; then
        local deleted_count=0
        
        # Find and delete old backups
        while IFS= read -r -d '' file; do
            rm -f "$file"
            ((deleted_count++))
        done < <(find "$BACKUP_DIR" -name "telegram-bot-backup-*" -type f -mtime +"$RETENTION_DAYS" -print0)
        
        if [ $deleted_count -gt 0 ]; then
            log "Deleted $deleted_count old backup files"
        else
            log "No old backups to delete"
        fi
    fi
}

# Restore from backup
restore() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    warn "⚠️ This will overwrite existing data!"
    read -p "Are you sure you want to restore from $backup_file? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restore cancelled"
        return 0
    fi
    
    log "Restoring from backup: $backup_file"
    
    # Stop bot if running
    if docker ps -q -f name="telegram-calendar-bot" | grep -q .; then
        log "Stopping bot..."
        docker-compose down
    fi
    
    # Extract backup
    tar -xzf "$backup_file"
    
    log "✅ Restore complete"
    log "You may need to restart the bot: ./scripts/deploy.sh dev"
}

# List available backups
list_backups() {
    log "Available backups:"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -name "telegram-bot-backup-*.tar.gz" -type f -printf "%T@ %Tc %f\n" | sort -n | while read timestamp date time file; do
            size=$(du -h "$BACKUP_DIR/$file" | cut -f1)
            echo "  📦 $file ($size) - $date $time"
        done
    else
        warn "No backup directory found"
    fi
    echo ""
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    log "Verifying backup integrity: $backup_file"
    
    if tar -tzf "$backup_file" >/dev/null 2>&1; then
        log "✅ Backup integrity OK"
        
        # Show contents
        echo ""
        log "Backup contents:"
        tar -tzf "$backup_file" | head -20
        
        local total_files=$(tar -tzf "$backup_file" | wc -l)
        if [ $total_files -gt 20 ]; then
            echo "  ... and $((total_files - 20)) more files"
        fi
        
        return 0
    else
        error "❌ Backup file is corrupted"
        return 1
    fi
}

# Print usage
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  create              Create a new backup"
    echo "  restore <file>      Restore from backup file"
    echo "  list                List available backups"
    echo "  verify <file>       Verify backup integrity"
    echo "  cleanup             Remove old backups"
    echo ""
    echo "Options:"
    echo "  --retention-days N  Set retention period (default: $RETENTION_DAYS)"
    echo ""
    echo "Examples:"
    echo "  $0 create                                           # Create backup"
    echo "  $0 restore backups/telegram-bot-backup-20231201_143000.tar.gz"
    echo "  $0 list                                             # List all backups"
    echo "  $0 cleanup --retention-days 7                      # Keep only 7 days"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

# Main command handling
case "${1:-create}" in
    "create")
        setup_backup_dir
        backup_data
        backup_volumes
        backup_database
        create_manifest
        cleanup_old_backups
        
        echo ""
        log "✅ Backup process complete!"
        list_backups
        ;;
    "restore")
        restore "$2"
        ;;
    "list")
        list_backups
        ;;
    "verify")
        verify_backup "$2"
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "help"|"--help"|"-h")
        usage
        ;;
    *)
        error "Unknown command: $1"
        usage
        exit 1
        ;;
esac