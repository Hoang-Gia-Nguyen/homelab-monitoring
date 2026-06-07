# CI Monitor Setup

The CI Monitor is a custom Prometheus exporter that exposes GitHub Actions CI status as metrics.

## Prerequisites

- Python 3.x installed on the host
- GitHub CLI (`gh`) installed and authenticated
- The exporter must run on the host (not in a container) to access `gh` CLI

## Running the Exporter

### Manual Start

Run the exporter on the host machine:

```bash
cd scripts
./ci_monitor_exporter.py
```

The exporter will start listening on port 9108 by default.

### Custom Port

To use a different port:

```bash
./ci_monitor_exporter.py 9109
```

### Running as a Background Service

#### Using nohup (Simple)

```bash
nohup python3 scripts/ci_monitor_exporter.py > ci_monitor.log 2>&1 &
```

#### Using systemd (Linux)

Create `/etc/systemd/system/ci-monitor.service`:

```ini
[Unit]
Description=CI Monitor Prometheus Exporter
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/homelab-monitoring
ExecStart=/usr/bin/python3 /path/to/homelab-monitoring/scripts/ci_monitor_exporter.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ci-monitor
sudo systemctl start ci-monitor
```

## Verifying Setup

1. Check that the exporter is running:
   ```bash
   curl http://localhost:9108/metrics
   ```

2. You should see output like:
   ```
   # HELP github_actions_ci_success Latest CI run status (1=success, 0=failure)
   # TYPE github_actions_ci_success gauge
   github_actions_ci_success 1
   ```

3. Check Prometheus is scraping the metrics:
   - Open http://localhost:9090
   - Go to Status → Targets
   - Look for the `ci_monitor` job
   - Status should show "UP"

## Troubleshooting

### "gh CLI not installed" message

Install and authenticate GitHub CLI:
```bash
# Install gh (varies by OS)
brew install gh  # macOS
# or
sudo apt install gh  # Ubuntu/Debian

# Authenticate
gh auth login
```

### Metrics showing 0 (failure) when CI is passing

- Check `gh` authentication: `gh auth status`
- Verify CI runs are visible: `gh run list -L 1`
- Check exporter logs for errors

### Prometheus not scraping

- Verify exporter is accessible: `curl http://localhost:9108/metrics`
- Check prometheus.yml has correct target: `host.docker.internal:9108`
- Restart Prometheus: `docker compose restart prometheus`
