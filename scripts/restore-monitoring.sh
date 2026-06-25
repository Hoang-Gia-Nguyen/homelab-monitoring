#!/bin/bash
# Restore script for homelab monitoring Docker volumes.
# Restores prometheus_data and grafana_data from a backup archive.

set -euo pipefail

COMPOSE_DIR="${COMPOSE_DIR:-.}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

usage() {
    echo "Usage: $0 [options] <backup-file>"
    echo ""
    echo "Restore Prometheus and Grafana volumes from a backup archive."
    echo ""
    echo "Positional:"
    echo "  backup-file          Path to the backup tar.gz file"
    echo ""
    echo "Options:"
    echo "  -d, --dry-run        Show what would be done without doing it"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "The script will prompt for confirmation before making changes."
    exit 0
}

DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage ;;
        *) BACKUP_FILE="$1"; shift ;;
    esac
done

if [ -z "${BACKUP_FILE:-}" ]; then
    echo "Error: backup file is required."
    usage
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: backup file not found: $BACKUP_FILE"
    exit 1
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "Backup file: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"

# Extract volume name from filename
BASENAME=$(basename "$BACKUP_FILE")
VOLUME_PREFIX="${BASENAME%_*}"  # e.g., "prometheus_data" or "grafana_data"

if [[ "$VOLUME_PREFIX" != "prometheus_data" && "$VOLUME_PREFIX" != "grafana_data" ]]; then
    echo "Error: unrecognized volume prefix '$VOLUME_PREFIX' in backup filename."
    echo "Expected filenames like 'prometheus_data_YYYY-MM-DD_HHMMSS.tar.gz'"
    echo "or 'grafana_data_YYYY-MM-DD_HHMMSS.tar.gz'"
    exit 1
fi

FULL_VOLUME_NAME="homelab-monitoring_${VOLUME_PREFIX}"

echo ""
echo "⚠️  WARNING: This will overwrite the contents of volume '$FULL_VOLUME_NAME'."
echo "   The monitoring stack should be stopped before restoring."
echo ""
read -p "Are you sure you want to continue? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Restore cancelled."
    exit 0
fi

log "Stopping monitoring stack..."
if $DRY_RUN; then
    log "[DRY-RUN] docker compose -f $COMPOSE_DIR/docker-compose.yml down"
else
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" down
    log "Stack stopped."
fi

log "Restoring volume '$FULL_VOLUME_NAME' from '$BACKUP_FILE'..."
if $DRY_RUN; then
    log "[DRY-RUN] docker run --rm -v ${FULL_VOLUME_NAME}:/volume -v ${BACKUP_DIR}:/backup alpine tar xzf /backup/$(basename $BACKUP_FILE) -C /volume"
else
    docker run --rm \
        -v "${FULL_VOLUME_NAME}:/volume" \
        -v "$(dirname "$BACKUP_FILE"):/backup" \
        alpine tar xzf "/backup/$(basename "$BACKUP_FILE")" -C /volume
    log "Restore complete."
fi

log "Restarting monitoring stack..."
if $DRY_RUN; then
    log "[DRY-RUN] docker compose -f $COMPOSE_DIR/docker-compose.yml up -d"
else
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" up -d
    log "Stack restarted."
fi

log "Restore finished. Check the logs for any errors."
