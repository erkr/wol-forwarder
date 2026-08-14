![image](./wol_forward_app/logo.png)

# Forward Wake-on-LAN packets on your LAN (App/Add-on)

This App (add-on) for Home Assistant provides a small daemon to forward Wake-on-LAN (WOL) magic packets on your LAN. Forwarding is protected by SecureOn, with optionally Host (source) and MAC (target) filtering.

Use case:
- Enable WOL remotely from the internet in a more secure way.
- Many routers deliberately don't support forwarding broadcasts and only forward to a specific IP/port on the LAN.
- Broadcasts can be abused for DDoS, so opening the standard WOL ports (7 or 9) on the internet is not ideal.
- Forwarding should only be allowed when the packet is at least authenticated by SecureOn.
- Optionally filter on sources (hosts) and / or targets (MAC)

What WOL Forwarder offers:
- Your router forwards UDP packets from an arbitrary external port (typically >50000) to this WOL forwarder daemon.
- The daemon checks whether the incoming UDP packet is a valid WOL packet and validates the SecureOn password.
- Lists of known sources (hosts) and targets (mac) can be defined and optionally used for filtering
- Only legimit packets are broadcast on the local network (on wol_port). Here the SecureOn suffix is removed before broadcasting.
- Optional HTTP API for monitoring forwarder status and packet statistics.

There are numerous WOL apps that can send magic packets with a SecureOn password. 
Note: Home Assistant's WOL integration can also send SecureOn packets.

## Usage

1. Install this add-on (add this repository as a custom add-on in Home Assistant Supervisor).
2. Configure options in the Supervisor add-on UI (or in `/data/options.json`):
   - `wol_port`: UDP port to send magic packets to on the LAN (default: 9)
   - `secure_on`: A string of exactly 12 hex characters (6 bytes, e.g. "aabbccddeeff") used as SecureOn password
   - `broadcast_ip`: IP address used for the broadcast (default: "255.255.255.255")
   - `known_hosts`: Optional list of hostnames. If provided, the add-on will resolve these hostnames for logging/reporting and optionally filtering
      - `host_filtering`: only accept packets whose source IP matches one of the resolved addresses in the known host list
   - `mac_list`: Optional list of know target addresses (mac - name pairs) for logging/reporting and optionally filtering
      - `mac_filtering`: Use the mac list for packet filtering as well. Only know targets will be forwarded
   - `dns_ttl`: DNS cache TTL in seconds (default: 300). Successful DNS results are refreshed only after this interval. When DNS refresh fails, the add-on keeps the last successful resolution
   - `http_api_enabled`: Enable HTTP API for status monitoring (default: false)
      - `api_port`: HTTP port for the status API (default: 5000)
   - `webhook_id`: When defined, data for forwarded packets will be posted
      - `ha_api_url`: When specified, it overrules the internal url to post webhooks (example: http://homeassistant.local:8123/api). Can als be used to post to other desitinations, as long no autorisation is required
      - `webhook_sel`: Options are `all`, `forward`, `reject` or `disable` (no reporting). Default is `forward`.
3. Review the netwerk options:
   - `listen_port`: UDP port the add-on listens on for forwarded packets from your router (default: 58090)
   - `api_port`: Don't enable, uless you understand the risks. This API HTTP port for the status endpoints. 
      Note it can be used safely from Home assistant without enabling this setting (after enabling `http_api_enabled`)!
      Home assistant should use the internal app/addon slug (e.g.: http://ab353c6f-wol-forward-app:8080)
      Only expose this port for LAN access for testing, as this API runs on a very leight weight non-secure webserver!

Note: Two config option moved to network senntings since v1.2.0:
 - api_port
 - listen_port 

## Example default (minimum) config:
```
wol_port: 9
listen_port: 58090
secure_on: a1:b2:c3:d4:e5:f6
broadcast_ip: 255.255.255.255
known_hosts: []
host_filtering: false
mac_list: []
mac_filtering: false
dns_ttl: 300
http_api_enabled: false
webhook_id: ''
```

## Example full config
```
log_level: warning
wol_port: 9
secure_on: a1:b2:c3:d4:e5:f6
broadcast_ip: 255.255.255.255
known_hosts:
  - host: 192.168.178.19
    name: iPhone Dad
  - host: 192.168.178.16
    name: iPhone Mom
  - host: my.ddns.net
    name: Utah
host_filtering: true
mac_list:
  - mac: 1A:2B:3C:4D:5E:6F
    name: MediaTower
  - mac: ec:43:f6:aa:78:6a
    name: My NAS
mac_filtering: true
dns_ttl: 300
http_api_enabled: false
webhook_id: -ExxxxxxxxxxxxxxxxHs
ha_api_url: http://homeassistant:8123/api
webhook_sel: all
```
## Installation

To install this third-party add-on:

Open Home Assistant > Settings > Add-ons > Add-on Store.
Click the menu (three dots in the top-right corner) and select Repositories.
Paste the GitHub repository link into the field at the bottom:
``` 
https://github.com/erkr/wol-forwarder
``` 
Refresh the page if needed. The add-on will appear under `Wake On Lan forward Repository`.

## HTTP Status API

When `http_api_enabled` is set to `true`, the add-on exposes a REST API for monitoring. The API runs on port `api_port` (default: 5000) on localhost.

### API Endpoints

- `GET /config` — Retrieve the configuration passed to the app.
- `GET /health` — Quick health check (HTTP 200 if running, 503 if stopped)
- `GET /stats` — Retrieve Packet statistics 
- `GET /dns` — Retrieve the current DNS cache 

### Config Response Example

```json
{
  "success": true,
  "data": {
    "running": true,
    "listen_address": "0.0.0.0",
    "listen_port": 58090,
    "wol_port": 9,
    "broadcast_ip": "255.255.255.255",
    "known_hosts": [{"host":"sender.example.com", "name": "friendly name"}],
    "host_filtering": true,
    "mac_list": [{"mac":"EC:43:F6:AA:78:6A", "name": "my NAS"}],
    "mac_filtering": false,
    "http_api_enabled": true,
    "webhook_reporting": {
      "forwarded": true,
      "rejected": false
    }
  }
}
```

### Health Response Example

```
{
  "listening": true,
  "status": "ok"
}
```

### Stats Response Example

```
{
    "packets": {
      "received": 42,
      "accepted": 40,
      "rejected": 2,
      "forwarded": 40
    }
}
```

### DNS Response Example

```
{
    "dns_cache": {
      "sender.example.com": {
        "ips": ["203.0.113.5"],
        "name": "friendly name",
        "resolved": true,
        "last_success": 1722812735.123,
        "last_attempt": 1722812735.456
      }
    }
}
```

## Webhook (optionally)
Wol Forwarder can post a webhooks when a valid packet was forwared and/or rejected.
This requirs `webhook_id` to bedefined and optionally a configured external url (`ha_api_url`).
Use `webhook_sel` to select what is reported (default reports forwarded packets).
Note: due a bug in HA, webhooks posted internally to Home Assistant (default when `ha_api_url` not defined) 
      only work when the webhook is defined with `local_only=false` (There will be no errors in the app log, as the call returns success!)
WebHook 'forwarded' posts contain JSON payload data with additional soruce and target info:
```
{
   "event":"forwarded", 
   "source_ip": source_ip, 
   "source_name": source_name, 
   "mac_address": mac_address, 
   "mac_name": mac_name 
}
```
WebHook 'rejected' posts contain JSON payload data with the reason of rejection:
```
{
   "event":"rejected", 
   "message": "reason", 
   "rejected": number,
   "accepted": number
}
```

Note: when host or mac addresses are not known, the adresses and names will be equal.
 
### Home Assistant Integration Examples

#### Webhook in Automation
Example of handling webhooks posted by WoL Forwarder. 
  
```yaml
alias: Handle WoL webhook
description: ''
triggers:
  - trigger: webhook
    allowed_methods:
      - POST
    local_only: false
    webhook_id: -ExxxxxxxxxxxxxxxxHs
conditions: []
actions:
  - choose:
      - conditions:
          - condition: template
            value_template: '{{ trigger.json.event == ''forwarded'' }}'
        sequence:
          - action: notify.send_message
            metadata: {}
            target:
              entity_id: notify.iphone
            data:
              title: '{{ ''WOL: ''~trigger.json.event}}'
              message: >-
                {{'Target '~trigger.json.mac_name~' Waked by
                '~trigger.json.source_name}}
        alias: Forwarded packets
      - conditions:
          - condition: template
            value_template: '{{ trigger.json.event == ''rejected'' }}'
        sequence:
          - action: notify.send_message
            metadata: {}
            target:
              entity_id: notify.iphone
            data:
              title: '{{ ''WOL: ''~trigger.json.event}}'
              message: '{{''Rejected ''~trigger.json.message }}'
        alias: Rejected packets

```
Notes:
  - make sure the webhook id used matches with the configured one
  - Without external HA URL configured, `local_only` must be set to `false` (bug in supervisor proxy, loosing the source IP)

        
#### REST Sensor for Health Check

```yaml
rest:
  - resource: http://localhost:58080/health
    scan_interval: 30
    sensor:
      - name: WOL Forwarder Health
        unique_id: wol_forwarder_health
        json_attributes:
          - listening
        value_template: "{{ value_json.status }}"
```

#### REST Sensor for Full Stats

```yaml
rest:
  - resource: http://localhost:58080/stats
    scan_interval: 60
    sensor:
      - name: WOL Forwarder Stats
        unique_id: wol_forwarder_stats
        json_attributes:
          - data
        value_template: "{{ 'ok' if value_json.success else 'error' }}"
```

## Notes

- Make sure your router forwards the external UDP port you choose to the Home Assistant host on `listen_port`.
- Ensure the target device's NIC supports Wake-on-LAN and that WOL is enabled in firmware/BIOS.
- The HTTP API is disabled by default. Enable if you need monitoring.
- API access is restricted to internal HA docker network by default. Do not expose the API to external networks (except testing).

## Author

- Erkr
