#!/usr/bin/env python3
"""
Simple HTTP server that exposes ci_monitor.sh metrics for Prometheus scraping.
Listens on port 9108 by default.
"""

import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                # Run the ci_monitor.sh script
                script_path = Path(__file__).parent / 'ci_monitor.sh'
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                
                # Send the script output as metrics
                self.wfile.write(result.stdout.encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}\n".encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging or customize as needed
        sys.stdout.write("%s - - [%s] %s\n" %
                        (self.client_address[0],
                         self.log_date_time_string(),
                         format % args))


def run_server(port=9108):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MetricsHandler)
    print(f"CI Monitor exporter listening on port {port}")
    print(f"Metrics available at http://localhost:{port}/metrics")
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9108
    run_server(port)
