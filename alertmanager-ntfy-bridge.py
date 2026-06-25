#!/usr/bin/env python3
"""
Alertmanager webhook bridge to ntfy notification service.

Receives webhook payloads from Prometheus Alertmanager and forwards
them as push notifications via ntfy.
"""
import logging
import sys
from flask import Flask, request
import requests
import json

# Configure structured logging
logger = logging.getLogger("alertmanager-ntfy-bridge")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
)
logger.addHandler(handler)

app = Flask(__name__)
NTFY_URL = "https://ntfy.hgnlab.org/homelab-alerts"


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    status = data.get('status', 'unknown')
    alert_count = len(data.get('alerts', []))

    logger.info(
        "Received webhook: status=%s alerts=%d",
        status, alert_count,
    )

    for alert in data.get('alerts', []):
        alertname = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'info')
        summary = alert['annotations'].get('summary', 'No summary')
        description = alert['annotations'].get('description', '')

        # Format message
        title = f"🔔 {alertname}" if status == 'firing' else f"✅ {alertname} Resolved"
        message = f"{summary}\n\n{description}".strip()

        # Set priority based on severity
        priority_map = {'critical': 5, 'warning': 3, 'info': 1}
        priority = priority_map.get(severity, 3)

        # Send to ntfy with proper formatting
        try:
            resp = requests.post(
                NTFY_URL,
                data=message.encode('utf-8'),
                headers={
                    'Title': title,
                    'Priority': str(priority),
                    'Tags': f'{severity},alert',
                },
                timeout=10,
            )
            resp.raise_for_status()
            logger.info(
                "Forwarded alert '%s' (status=%s, severity=%s) to ntfy — HTTP %d",
                alertname, status, severity, resp.status_code,
            )
        except requests.RequestException as e:
            logger.error(
                "Failed to forward alert '%s' to ntfy: %s",
                alertname, e,
            )

    return 'OK', 200


@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200


if __name__ == '__main__':
    logger.info("Starting Alertmanager ntfy bridge on port 5001")
    app.run(host='0.0.0.0', port=5001)
