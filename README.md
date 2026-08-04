# WOL Forwarder Home Assistant Add-on

This add-on provides a small daemon to forward Wake-on-LAN (WOL) magic packets on your LAN.

Use case:
- Enable WOL remotely from the internet in a more secure way.
- Many routers deliberately don't support forwarding broadcasts and only forward to a specific IP/port on the LAN.
- Broadcasts can be abused for DDoS, so opening the standard WOL ports (7 or 9) on the internet is not ideal.
- Forwarding should only be allowed when the packet is authenticated (SecureOn).

What WOL Forwarder offers:
- Your router forwards UDP packets from an arbitrary external port (typically >50000) to this WOL forwarder daemon.
- The daemon checks whether the incoming UDP packet is a valid WOL packet and validates the SecureOn password.
- Only valid packets are broadcast on the local network (on wol_port) — the SecureOn suffix is removed before broadcasting.

There are numerous WOL apps that can send magic packets with a SecureOn password. Home Assistant's WOL integration can also send SecureOn packets.

Usage
1. Install this add-on (add this repository as a custom add-on in Home Assistant Supervisor).
2. Configure options in the Supervisor add-on UI (or in `/data/options.json`):
   - `wol_port`: UDP port to send magic packets to on the LAN (default: 9)
   - `listen_port`: UDP port the add-on listens on for forwarded packets from your router (default: 58090)
   - `secure_on`: A string of exactly 12 hex characters (6 bytes, e.g. "aabbccddeeff") used as SecureOn password
   - `broadcast_ip`: IP address used for the broadcast (default: "255.255.255.255")
   - `allowed_hosts`: Optional list of hostnames. If provided, the add-on will resolve these hostnames and only accept packets whose source IP matches one of the resolved addresses (backwards compatible: leave empty to allow all sources).
   - `dns_ttl`: DNS cache TTL in seconds (default: 300). Successful DNS results are refreshed only after this interval. When DNS refresh fails, the add-on keeps the last successful resolution for that host to avoid transient DNS outages.

Example options.json
```json
{
  "wol_port": 9,
  "listen_port": 58090,
  "secure_on": "aabbccddeeff",
  "broadcast_ip": "255.255.255.255",
  "allowed_hosts": ["sender.example.com"],
  "dns_ttl": 300
}
```

Notes
- Host network mode is required so broadcast packets reach the LAN. This add-on's `config.json` sets `host_network: true`.
- Make sure your router forwards the external UDP port you choose to the Home Assistant host on `listen_port`.
- Ensure the target device's NIC supports Wake-on-LAN and that WOL is enabled in firmware/BIOS.

Testing
- Local test: set `allowed_hosts` to `["localhost"]` in options and run the add-on on the host; sending a SecureOn WOL packet from 127.0.0.1 should be accepted.
- Fallback behavior: if a host resolved successfully in the past but a later DNS refresh fails, the add-on keeps the previous IPs and continues allowing those sources until the next successful refresh (or until the admin changes configuration).
- Logs:
  - Successful resolution: debug "Resolved <host> -> {ips}"
  - Failed refresh but keeping previous IPs: warning with details
  - Rejected packet because not allowed: warning "Dropping packet from ... — source not allowed"

Author
- erkr
