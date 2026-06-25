#!/bin/bash
# Backup script for homelab monitoring Docker volumes.
# Creates timestamped compressed archives of prometheus_data and grafana_data.

set -euo pipefail

# Configurable defaults
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPOSE_DIR="${COMPOSE_DIR:-.}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Backup Prometheus and Grafana Docker volumes."
    echo ""
    echo "Options:"
    echo "  -o, --output DIR     Backup directory (default: ./backups)"
    echo "  -r, --retention DAYS Retention period in days (default: 30)"
    echo "  -c, --compose DIR    Docker Compose project directory (default: .)"
    echo "  -s, --stop           Stop the stack before backup (recommended)"
    echo "  -d, --dry-run        Show what would be done without doing it"
    echo "  -h, --help           Show this help message"
    exit 0
}

DRY_RUN=false
STOP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output) BACKUP_DIR="$2"; shift 2 ;;
        -r|--retention) RETENTION_DAYS="$2"; shift 2 ;;
        -c|--compose) COMPOSE_DIR="$2"; shift 2 ;;
        -s|--stop) STOP=true; shift ;;
        -d|--dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Stop stack if requested
if $STOP; then
    log "Stopping monitoring stack..."
    if $DRY_RUN; then
        log "[DRY-RUN] docker compose -f $COMPOSE_DIR/docker-compose.yml down"
    else
        docker compose -f "$COMPOSE_DIR/docker-compose.yml" down
        log "Stack stopped."
    fi
fi

# Backup function using docker run --rm with alpine
backup_volume() {
    local volume_name="$1"
    local backup_file="$BACKUP_DIR/${volume_name}_${TIMESTAMP}.tar.gz"

    log "Backing up volume: $volume_name -> $backup_file"
    if $DRY_RUN; then
        log "[DRY-RUN] docker run --rm -v ${volume_name}:/volume -v ${BACKUP_DIR}:/backup alpine tar czf /backup/$(basename $backup_file) -C /volume ."
    else
        docker run --rm \
            -v "${volume_name}:/volume:ro" \
            -v "${BACKUP_DIR}:/backup" \
            alpine tar czf "/backup/$(basename "$backup_file")" -C /volume .
        log "Backup complete: $(ls -lh "$backup_file" | awk '{print $5}')"
    fi
}

backup_volume "homelab-monitoring_prometheus_data"
backup_volume "homelab-monitoring_grafana_data"

# Restart stack if it was stopped
if $STOP; then
    log "Restarting monitoring stack..."
    if $DRY_RUN; then
        log "[DRY-RUN] docker compose -f $COMPOSE_DIR/docker-compose.yml up -d"
    else
        docker compose -f "$COMPOSE_DIR/docker-compose.yml" up -d
        log "Stack restarted."
    fi
fi

# Prune old backups
log "Pruning backups older than $RETENTION_DAYS days..."
if $DRY_RUN; then
    log "[DRY-RUN] find $BACKUP_DIR -name '*.tar.gz' -mtime +$RETENTION_DAYS -delete"
else
    find "$BACKUP_DIR" -name '*.tar.gz' -mtime "+$RETENTION_DAYS" -delete
    log "Pruning complete."
fi

log "Backup finished successfully."
