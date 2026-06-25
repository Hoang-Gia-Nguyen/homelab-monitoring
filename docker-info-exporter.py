#!/usr/bin/env python3
"""
Docker container info exporter for Prometheus.
Connects to Docker daemon via Unix socket and exposes container
ID -> name/image/state mappings for Prometheus to join with cadvisor.
"""
import os
import json
import time
import http.server
import urllib.request

DOCKER_SOCK = os.environ.get("DOCKER_SOCK", "/var/run/docker.sock")
LISTEN_ADDR = os.environ.get("LISTEN_ADDR", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "9108"))
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "15"))

containers = {}

def docker_api(path):
    """Call Docker API via Unix socket and return parsed JSON."""
    import http.client
    sock = None
    try:
        sock = __import__('socket').socket(__import__('socket').AF_UNIX, __import__('socket').SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(DOCKER_SOCK)
        conn = http.client.HTTPConnection("localhost", timeout=5)
        conn.sock = sock
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read().decode()
        conn.close()
        return json.loads(body)
    except Exception as e:
        print(f"[docker-info-exporter] Docker API error ({path}): {e}")
        return None

def update_containers():
    global containers
    data = docker_api("/containers/json?all=true")
    if data is None:
        return
    new_map = {}
    for c in data:
        cid = c.get("Id", "")[:12]
        names = c.get("Names", [])
        name = names[0].lstrip("/") if names else cid[:12]
        image = c.get("Image", "unknown")
        state = c.get("State", "unknown")
        new_map[cid] = {
            "name": name,
            "full_id": c.get("Id", ""),
            "image": image,
            "state": state,
        }
    containers = new_map
    print(f"[docker-info-exporter] Updated: {len(containers)} containers tracked", flush=True)

def generate_metrics():
    lines = []
    lines.append("# HELP docker_container_info Docker container metadata")
    lines.append("# TYPE docker_container_info gauge")
    for cid, info in sorted(containers.items()):
        name = info["name"].replace('"', '\\"').replace("\n", " ")
        image = info["image"].replace('"', '\\"').replace("\n", " ")
        state = info["state"].replace('"', '\\"')
        lines.append(
            f'docker_container_info{{container_id="{cid}",'
            f'container_name="{name}",'
            f'image="{image}",'
            f'state="{state}"}} 1'
        )
    lines.append("")
    return "\n".join(lines)

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            payload = generate_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload.encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    # Initial fetch
    print(f"[docker-info-exporter] Connecting to Docker at {DOCKER_SOCK}", flush=True)
    update_containers()

    # Periodic refresh
    import threading
    def refresh_loop():
        while True:
            time.sleep(REFRESH_INTERVAL)
            update_containers()
    t = threading.Thread(target=refresh_loop, daemon=True)
    t.start()

    # HTTP server
    server = http.server.HTTPServer((LISTEN_ADDR, LISTEN_PORT), MetricsHandler)
    print(f"[docker-info-exporter] Listening on {LISTEN_ADDR}:{LISTEN_PORT}", flush=True)
    server.serve_forever()
