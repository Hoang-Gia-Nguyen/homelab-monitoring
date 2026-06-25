# Backup & Restore

This directory contains scripts to backup and restore the homelab monitoring
stack's persistent data (Prometheus TSDB and Grafana data).

## Overview

The stack uses two Docker volumes:
- `homelab-monitoring_prometheus_data` — Prometheus time-series database
- `homelab-monitoring_grafana_data` — Grafana dashboards, settings, and SQLite DB

## Backup

### Quick backup (online, no downtime)

```bash
./scripts/backup-monitoring.sh
```

Creates timestamped archives in `./backups/` by default:

```
backups/
├── homelab-monitoring_prometheus_data_2026-06-25_030000.tar.gz
└── homelab-monitoring_grafana_data_2026-06-25_030000.tar.gz
```

### Consistent backup (with downtime)

```bash
./scripts/backup-monitoring.sh --stop
```

Stops the stack before backing up to ensure data consistency.

### Custom options

```bash
./scripts/backup-monitoring.sh \
  --output /path/to/backups \
  --retention 14 \
  --compose /path/to/project
```

- `--output`: backup directory (default: `./backups`)
- `--retention`: days to keep backups (default: 30)
- `--stop`: stop the stack before backup
- `--dry-run`: preview without making changes
- `--compose`: path to docker-compose.yml directory

### Prometheus TSDB snapshot (alternative)

For a safer alternative to file-level backup, use the Prometheus HTTP API:

```bash
# Create a snapshot (while Prometheus is running)
curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot

# The snapshot is stored inside the prometheus_data volume under
# /prometheus/snapshots/. Copy it with:
docker run --rm \
  -v homelab-monitoring_prometheus_data:/volume:ro \
  -v /tmp/backup:/backup \
  alpine cp -r /volume/snapshots /backup/
```

## Restore

### Manual restore

```bash
# Stop the stack
docker compose down

# Restore a specific backup
./scripts/restore-monitoring.sh backups/prometheus_data_2026-06-25_030000.tar.gz

# Restart the stack
docker compose up -d
```

The restore script will:
1. Prompt for confirmation
2. Stop the stack
3. Overwrite the target volume with backup data
4. Restart the stack

### Dry-run

```bash
./scripts/restore-monitoring.sh --dry-run backups/*.tar.gz
```

## Scheduling

### Cron (daily backup at 3 AM)

```cron
0 3 * * * cd /path/to/homelab-monitoring && ./scripts/backup-monitoring.sh --output /mnt/backups/monitoring --retention 30
```

### systemd timer

Create `/etc/systemd/system/monitoring-backup.service`:

```ini
[Unit]
Description=Homelab monitoring backup
After=docker.service

[Service]
Type=oneshot
ExecStart=/path/to/homelab-monitoring/scripts/backup-monitoring.sh --output /mnt/backups/monitoring --retention 30
WorkingDirectory=/path/to/homelab-monitoring
```

Create `/etc/systemd/system/monitoring-backup.timer`:

```ini
[Unit]
Description=Daily monitoring backup

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now monitoring-backup.timer
```

## Offsite / Cold Storage

For disaster recovery, periodically rsync or copy backups to offsite storage:

```bash
rsync -avz /mnt/backups/monitoring/ backup-user@offsite-host:/backups/monitoring/
```

Recommended retention:
- Local: 30 days
- Offsite: 90 days
- Quarterly archive: 1 year
