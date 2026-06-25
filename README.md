# Homelab Monitoring

A Docker Compose-based monitoring stack for homelab infrastructure.

## Services

- **Prometheus** — Metrics collection and alerting
- **Alertmanager** — Alert management and routing
- **Grafana** — Dashboards and visualization
- **cAdvisor** — Container metrics
- **Blackbox Exporter** — Synthetic health checks
- **Loki + Promtail** — Log aggregation
- **Alertmanager Bridge** — Webhook → ntfy push notification bridge

## Quick Start

```bash
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

## Documentation

- [Backup & Restore](BACKUP.md)
- [CI Monitor Setup](CI_MONITOR_SETUP.md)

## Backup

See [BACKUP.md](BACKUP.md) for backup and restore procedures.
