# Pull Request

## Description
Add HTTP status API endpoint for monitoring WOL forwarder operations.

## Changes
- Flask-based HTTP server exposing `/status`, `/health`, `/stats`, and `/dns` endpoints
- Real-time packet statistics tracking (received, accepted, rejected, forwarded)
- DNS cache state monitoring with resolution status per host
- New configuration options: `http_api_enabled` and `api_port`
- Background API server runs without blocking UDP listener
- Thread-safe statistics and status data

## Configuration
The API is disabled by default. To enable:
1. Set `http_api_enabled: true` in add-on options
2. Configure `api_port` (default: 5000)
3. Restart the add-on

## API Endpoints
- `GET /status` — Full status with stats and DNS cache
- `GET /health` — Quick health check (200 if running, 503 if stopped)
- `GET /stats` — Packet statistics only
- `GET /dns` — DNS cache state only

## Example Response
```json
{
  "success": true,
  "data": {
    "running": true,
    "listen_port": 58090,
    "packets": {
      "received": 42,
      "accepted": 40,
      "rejected": 2,
      "forwarded": 40
    },
    "dns_cache": {
      "sender.example.com": {
        "ips": ["203.0.113.5"],
        "resolved": true,
        "last_success": 1722812735.123
      }
    }
  }
}
```

## Testing
- Enable `http_api_enabled` in add-on config
- Query `http://localhost:5000/status` to verify
- Check logs for API server startup messages
