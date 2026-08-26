![image](./wol_forward_app/logo.png)

# Forward Wake-on-LAN packets on your LAN (App/Add-on)
[![GitHub Release][releases-shield]][releases] [![License][license-shield]](./wol_forward_app/LICENSE)
![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield]

This App (add-on) for Home Assistant provides a small daemon to forward Wake-on-LAN (WoL) magic packets on your LAN. Forwarding is protected by SecureOn, with optionally Host (source) and MAC (target) filtering.

Use case:
- Enable WoL remotely from the internet in a more secure way.
- Many routers deliberately don't support forwarding broadcasts and only forward to a specific IP/port on the LAN.
- Broadcasts can be abused for DDoS, so opening the standard WoL ports (7 or 9) on the internet is not ideal.
- Forwarding should only be allowed when the packet is at least authenticated by SecureOn.
- Optionally filter on sources (hosts) and / or targets (MAC)

What WoL Forwarder offers:
- Your router forwards UDP packets from an arbitrary external port (typically >50000) to this WoL forwarder daemon.
- The daemon checks whether the incoming UDP packet is a valid WoL packet and validates the SecureOn password.
- Lists of known sources (hosts) and targets (mac) can be defined and optionally used for filtering
- Only legimit packets are broadcast on the local network (on wol_port). Here the SecureOn suffix is removed before broadcasting.
- Optional HTTP API for monitoring forwarder status and packet statistics.

There are numerous (mobile) WoL apps that can send magic packets with a SecureOn password. 
In examples there is a WakeOnLan shell script that can be used.
Home Assistant's native WoL integration can also send SecureOn extended packets.

## Usage

1. Install this add-on (add this repository as a custom add-on in Home Assistant Supervisor).
2. Configure options in the Supervisor add-on UI (or in `/data/options.json`):
   - `wol_port`: UDP port to send magic packets to on the LAN (default: 9)
   - `listen_port`: UDP port the add-on listens on for forwarded packets from your router (default: 58090)
   - `secure_on`: A string of exactly 12 hex characters (6 bytes, e.g. "aabbccddeeff") used as SecureOn password
   - `broadcast_ip`: IP address used for the broadcast (default: "255.255.255.255")
   - `known_hosts`: Optional list of hostnames. If provided, the add-on will resolve these hostnames for logging/reporting and optionally filtering
      - `host_filtering`: only accept packets whose source IP matches one of the resolved addresses in the known host list
   - `mac_list`: Optional list of know target addresses (mac - name pairs) for logging/reporting and optionally filtering
      - `mac_filtering`: Use the mac list for packet filtering as well. Only know targets will be forwarded
   - `dns_ttl`: DNS cache TTL in seconds (default: 300). Successful DNS results are refreshed only after this interval. When DNS refresh fails, the add-on keeps the last successful resolution
   - `http_api_expose`: Expose HTTP API for status monitoring on the Host network. (default: false, to allow local HA usage only)
      - `api_port`: HTTP port for the status API (default: 58080)
   - `webhook_id`: When defined, data for forwarded packets will be posted
      - `ha_api_url`: When specified, it overrules the internal url to post webhooks (example: http://homeassistant.local:8123/api). Can als be used to post to other desitinations, as long no autorisation is required
      - `webhook_sel`: Options are `all`, `forward`, `reject` or `disable` (no reporting). Default is `forward`.
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
http_api_expose: false
api_port: 58080
webhook_id: ''
```

## Example full config
```
log_level: warning
wol_port: 9
listen_port: 59990
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
http_api_expose: false
api_port: 59080
webhook_id: -ExxxxxxxxxxxxxxxxHs
ha_api_url: http://homeassistant:8123/api
webhook_sel: all
```
## Installation

Press this button to automatically add the WoL Forwarder Repro to your Home Assistant: [!["Add repository on Home Assistant"][add-repro-shield]](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Ferkr%2Fwol-forwarder)

If you want to do add the repository manually, please follow the procedure highlighted in the [Home Assistant website](https://www.home-assistant.io/common-tasks/os#installing-a-third-party-app-repository). Use the following URL to add this repository: [https://github.com/erkr/wol-forwarder](https://github.com/erkr/wol-forwarder)

Once this Wol-Forwarder repro is added to your Home Asssitant, Wol-Forwarder can be installed via the app store: [!["App store on Home Assistant"][app-store-shield]](https://my.home-assistant.io/redirect/supervisor_store/).
There are two versions:
- The stable release version (recommended)
- A dev version (for testing new features)

## HTTP Status API

When `http_api_expose` is set to `true`, the add-on exposes a REST API for monitoring on the Host LAN network. 
By default the API runs on the local HA internal network only, on port `api_port` (default: 58080).
Optionally enable `http_api_expose` when testing your setup, and keep disabled in normal operation
(it's a leightweight web server not suitable for regular use and shall never to be expose on untrusted networks).

### API Endpoints

- `GET /config` — Retrieve the configuration passed to the app.
- `GET /health` — Quick health check (HTTP 200 if running, 503 if stopped)
- `GET /stats` — Retrieve Packet statistics 
- `GET /dns` — Retrieve the current DNS cache 

Those endpoints can easily be queried by adding some shell commands in `config.yaml`:
``` 
shell_command:
# WoL Forward 
  wol_config: curl -s http://localhost:58080/config | jq "."
  wol_dns: curl -s http://localhost:58080/dns | jq "."
  wol_stats: curl -s http://localhost:58080/stats | jq "."
``` 
These commands will add actions that can be used in the `Tools->actions` menu

### Config Response Example

```json
{
  "success": true,
  "data": {
    "running": true,
    "loglevel": "DEBUG",
    "listen_address": "0.0.0.0",
    "listen_port": 58090,
    "wol_port": 9,
    "broadcast_ip": "255.255.255.255",
    "known_hosts": [{"host":"sender.example.com", "name": "friendly name"}],
    "host_filtering": true,
    "mac_list": [{"mac":"EC:43:F6:AA:78:6A", "name": "my NAS"}],
    "mac_filtering": false,
    "http_api_expose": false,
    "webhook_reporting": {
      "ha_api_url": "",
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
  "data": {
    "packets": {
      "accepted": 92,
      "forwarded": 92,
      "received": 101,
      "rejected": 9
    },
    "running": true
  },
  "success": true
}
```

### DNS Response Example

```
{
  "data": {
    "dns_cache": {
      "sender.example.com": {
        "ips": ["203.0.113.5"],
        "name": "friendly name",
        "resolved": true,
        "last_success": 1722812735.123,
        "last_attempt": 1722812735.456
      }
    },
    "running": true,
    "statistics": {
        "lookups": 4607,
        "success": 4591,
    }
  },
  "success": true
}
```

## Webhook (optionally)
Wol Forwarder can post a webhooks when a valid packet was forwared and/or rejected.
This requirs at least `webhook_id` to be defined and optionally an alternative external url (`ha_api_url`).
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
              entity_id: notify.my_iphone
            data:
              title: '{{ ''WOL: ''~trigger.json.event}}'
              message: >-
                {{'Target '~trigger.json.mac_name~' Waked by
                '~trigger.json.source_name}}
            enabled: false
        alias: Forwarded packets
      - conditions:
          - condition: template
            value_template: '{{ trigger.json.event == ''rejected'' }}'
        sequence:
          - action: notify.send_message
            metadata: {}
            target:
              entity_id: notify.my_iphone
            data:
              title: '{{ ''WOL: ''~trigger.json.event}}'
              message: '{{''Rejected ''~trigger.json.message }}'
            enabled: true
        alias: Rejected packets
mode: single

```
Notes:
  - make sure the webhook id used matches with the configured one
  - Without external HA URL configured, `local_only` must be set to `false` (bug in supervisor proxy, loosing the source IP)

        

## Notes

- Host network mode is required so broadcast packets reach the LAN. This add-on's `config.json` sets `host_network: true`.
- Make sure your router forwards the external UDP port you choose to the Home Assistant host on `listen_port`.
- Ensure the target device's NIC supports Wake-on-LAN and that WoL is enabled in firmware/BIOS.

## Author

- Erkr

[releases-shield]: https://img.shields.io/badge/release-v1.2.0-blue.svg
[add-repro-shield]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
[app-store-shield]: https://my.home-assistant.io/badges/supervisor_store.svg
[license-shield]: https://img.shields.io/badge/license-MIT-green.svg
[releases]: https://github.com/erkr/wol-forwarder/releases
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg

