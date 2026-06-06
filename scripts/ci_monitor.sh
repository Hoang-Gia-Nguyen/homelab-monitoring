#!/usr/bin/env bash
# Export GitHub Actions CI status as a Prometheus metric.
# Requires the GitHub CLI (gh) to be installed and authenticated.

set -euo pipefail

echo "# HELP github_actions_ci_success Latest CI run status (1=success, 0=failure)"
echo "# TYPE github_actions_ci_success gauge"

status=0

if command -v gh > /dev/null 2>&1; then
  conclusion=$(gh run list -L 1 --json conclusion --jq '.[0].conclusion' 2>/dev/null || true)
  if [[ "$conclusion" == "success" ]]; then
    status=1
  fi
else
  echo "# Unable to determine CI status: gh CLI not installed" >&2
fi

echo "github_actions_ci_success $status"
