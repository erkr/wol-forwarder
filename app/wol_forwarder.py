#!/usr/bin/env python3
"""
Simple WOL forwarder HTTP API.
- POST /wake with JSON {"mac": "aa:bb:cc:dd:ee:ff", "ip": "255.255.255.255", "port": 9}
- GET /ping returns 200 OK

Reads add-on options from /data/options.json when available (Supervisor).
"""

import json
import os
import socket
import struct
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Defaults (can be overridden by /data/options.json or env vars set by run.sh)
WOL_PORT = int(os.environ.get('WOL_PORT', 9))
HTTP_PORT = int(os.environ.get('HTTP_PORT', 8090))
LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'false').lower() in ('1', 'true', 'yes')
LOG_FILE = os.environ.get('LOG_FILE', '/config/wol-forwarder.log')
ALLOWED_IPS = None

# Try to load /data/options.json (Supervisor)
try:
    with open('/data/options.json', 'r') as f:
        opts = json.load(f)
        WOL_PORT = int(opts.get('wol_port', WOL_PORT))
        HTTP_PORT = int(opts.get('http_port', HTTP_PORT))
        LOG_TO_FILE = bool(opts.get('log_to_file', LOG_TO_FILE))
        LOG_FILE = opts.get('log_file', LOG_FILE)
        allowed = opts.get('allowed_ips', [])
        if isinstance(allowed, list) and allowed:
            ALLOWED_IPS = set(allowed)
except FileNotFoundError:
    pass
except Exception as e:
    print(f"Failed to parse /data/options.json: {e}", file=sys.stderr)


def log(msg):
    line = f"[wol-forwarder] {msg}"
    print(line)
    if LOG_TO_FILE:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(line + '\n')
        except Exception as e:
            print(f"Failed to write log: {e}", file=sys.stderr)


def create_magic_packet(mac: str) -> bytes:
    mac = mac.replace(':', '').replace('-', '').strip()
    if len(mac) != 12:
        raise ValueError('MAC must be 12 hex digits')
    data = bytes.fromhex(mac)
    return b'\xff' * 6 + data * 16


def send_magic_packet(mac: str, ip: str = '255.255.255.255', port: int = 9):
    packet = create_magic_packet(mac)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (ip, port))
    finally:
        sock.close()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _send(self, code=200, body=b''):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/ping':
            self._send(200, b'{"status": "ok"}')
        else:
            self._send(404, b'{"error": "not_found"}')

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/wake':
            self._send(404, b'{"error": "not_found"}')
            return

        length = int(self.headers.get('Content-Length', 0))
        if length <= 0:
            self._send(400, b'{"error": "no_body"}')
            return

        remote_ip = self.client_address[0]
        if ALLOWED_IPS is not None and remote_ip not in ALLOWED_IPS:
            log(f"Rejected request from {remote_ip}")
            self._send(403, b'{"error": "forbidden"}')
            return

        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode('utf-8'))
            mac = data.get('mac')
            ip = data.get('ip', '255.255.255.255')
            port = int(data.get('port', WOL_PORT))
            if not mac:
                raise ValueError('mac required')
            send_magic_packet(mac, ip, port)
            log(f"Sent magic packet to {mac} via {ip}:{port} (requested by {remote_ip})")
            self._send(200, b'{"status": "sent"}')
        except Exception as e:
            log(f"Error handling request: {e}")
            self._send(400, json.dumps({"error": "bad_request", "message": str(e)}).encode('utf-8'))

    def log_message(self, format, *args):
        # suppress default logging
        return


def run():
    server = HTTPServer(('0.0.0.0', HTTP_PORT), Handler)
    log(f"Starting WOL forwarder HTTP server on 0.0.0.0:{HTTP_PORT}, target WOL port {WOL_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    run()
