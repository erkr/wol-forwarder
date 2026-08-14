#!/bin/bash
# Entrypoint for the WOL Forwarder add-on
set -e

# Supervisor provides options in /data/options.json
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
  # Prefer top-level key, fall back to .options.<key>. Never read .schema.
  LOG_LEVEL=$(jq -r '(.log_level // .options.log_level) // "info"' "$OPTIONS_FILE")
  WOL_PORT=$(jq -r '(.wol_port // .options.wol_port) // 9' "$OPTIONS_FILE")
  BROADCAST_IP=$(jq -r '(.broadcast_ip // .options.broadcast_ip) // "255.255.255.255"' "$OPTIONS_FILE")
  SECURE_ON=$(jq -r '(.secure_on // .options.secure_on) // "a1:b2:c3:d4:e5:f6"' "$OPTIONS_FILE")
  KNOWN_HOSTS=$(jq -r '(.known_hosts // .options.known_hosts) // []' "$OPTIONS_FILE")
  HOST_FILTERING=$(jq -r '(.host_filtering // .options.host_filtering) // false' "$OPTIONS_FILE")
  MAC_LIST=$(jq -r '(.mac_list // .options.mac_list) // []' "$OPTIONS_FILE")
  MAC_FILTERING=$(jq -r '(.mac_filtering // .options.mac_filtering) // false' "$OPTIONS_FILE")
  DNS_TTL=$(jq -r '(.dns_ttl // .options.dns_ttl) // 300' "$OPTIONS_FILE")
  HTTP_API_ENABLED=$(jq -r '(.http_api_enabled // .options.http_api_enabled) // false' "$OPTIONS_FILE")
  WEBHOOK_ID=$(jq -r '(.webhook_id // .options.webhook_id) // ""' "$OPTIONS_FILE")
  WEBHOOK_SEL=$(jq -r '(.webhook_sel // .options.webhook_sel) // "forward"' "$OPTIONS_FILE")
  HA_API_URL=$(jq -r '(.ha_api_url // .options.ha_api_url) // ""' "$OPTIONS_FILE")
else
  LOG_LEVEL='info'
  WOL_PORT=9
  SECURE_ON="a1:b2:c3:d4:e5:f6"
  BROADCAST_IP="255.255.255.255"
  KNOWN_HOSTS="[]"
  HOST_FILTERING=false
  MAC_LIST="[]"
  MAC_FILTERING=false
  DNS_TTL=300
  HTTP_API_ENABLED=false
  WEBHOOK_ID=""
  HA_API_URL=""
  WEBHOOK_SEL="forward"
fi

# internal listen ports, mapped to external LAN ports in network settings (port mapping)
LISTEN_PORT=58090
API_PORT=8080

export LOG_LEVEL WOL_PORT BROADCAST_IP LISTEN_PORT SECURE_ON KNOWN_HOSTS HOST_FILTERING MAC_LIST MAC_FILTERING DNS_TTL HTTP_API_ENABLED API_PORT WEBHOOK_ID WEBHOOK_SEL HA_API_URL

exec python3 /usr/src/app/app/wol_forwarder.py
