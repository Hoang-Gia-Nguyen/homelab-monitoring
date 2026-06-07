#!/usr/bin/env python3
from flask import Flask, request
import requests
import json

app = Flask(__name__)
NTFY_URL = "https://ntfy.hgnlab.org/homelab-alerts"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    status = data.get('status', 'unknown')
    
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
        requests.post(NTFY_URL, 
            data=message.encode('utf-8'),
            headers={
                'Title': title,
                'Priority': str(priority),
                'Tags': f'{severity},alert'
            })
    
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
