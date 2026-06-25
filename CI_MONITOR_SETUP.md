# CI Monitor (Containerized)

The CI Monitor exposes GitHub Actions CI status as Prometheus metrics.
It runs as a Docker container in the monitoring stack.

## Prerequisites

- Docker Compose stack running
- GitHub token with `repo` read access

## Setup

1. Add your GitHub token to `.env`:

   ```env
   GH_TOKEN=github_pat_xxxxxxxxxxxx
   ```

2. The CI Monitor starts automatically with `docker compose up`.
   It exposes metrics on port **9109** (internal).

## Verifying Setup

1. Check the service is running:
   ```bash
   docker compose ps ci-monitor
   ```

2. Query the metrics:
   ```bash
   curl http://localhost:9109/metrics
   ```

3. Expected output:
   ```
   # HELP github_actions_ci_success Latest CI run status (1=success, 0=failure)
   # TYPE github_actions_ci_success gauge
   github_actions_ci_success 1
   ```

4. Check in Prometheus:
   - Open http://localhost:9090
   - Status → Targets
   - Look for job `ci_monitor` — should show "UP"

## Troubleshooting

### Metrics always show 0

- Verify your GitHub token is set in `.env`
- Run `docker compose logs ci-monitor` to check for errors
- Ensure the token has `repo` read scope

### Container not starting

- Run `docker compose build ci-monitor` to rebuild
- Check build logs for errors
