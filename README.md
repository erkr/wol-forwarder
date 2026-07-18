# WOL Forwarder Home Assistant Add-on

This add-on provides a small HTTP API to send Wake-on-LAN magic packets on your LAN.
It is intended to run with host networking so the broadcast packets reach your network.

Features
- POST /wake to send a magic packet for a given MAC address
- Optional IP allowlist
- Optional log-to-file under your Home Assistant config folder

Usage
1. Install this add-on (from this repository branch) in Home Assistant Supervisor.
2. Configure options in the Supervisor add-on UI:
   - wol_port: UDP port to send magic packets to (default 9)
   - http_port: Port for the HTTP API (default 8090). Note: add-on uses host network.
   - log_to_file: true/false
   - log_file: path to log file (e.g. /config/wol-forwarder.log)
   - allowed_ips: optional list of IP addresses allowed to call the API

HTTP API
- POST /wake
  Body (JSON): {"mac": "AA:BB:CC:DD:EE:FF", "ip": "255.255.255.255", "port": 9}
  ip and port are optional. ip defaults to 255.255.255.255.

- GET /ping
  Returns 200 OK with {"status": "ok"}

Example options.json
{
  "wol_port": 9,
  "http_port": 8090,
  "log_to_file": false,
  "log_file": "/config/wol-forwarder.log",
  "allowed_ips": ["192.168.1.100"]
}

Security
- The HTTP endpoint is unauthenticated by default. Use the allowed_ips option, a reverse proxy, or Home Assistant automation protections to limit access.

Notes
- Host network mode is recommended so broadcast packets reach the LAN.
