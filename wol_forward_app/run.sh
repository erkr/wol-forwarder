#!/bin/bash
# Entrypoint for the WOL Forwarder add-on
set -e

# Supervisor provides options in /data/options.json
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
  # Prefer top-level key, fall back to .options.<key>. Never read .schema.
  WOL_PORT=$(jq -r '(.wol_port // .options.wol_port) // 9' "$OPTIONS_FILE")
  BROADCAST_IP=$(jq -r '(.broadcast_ip // .options.broadcast_ip) // "255.255.255.255"' "$OPTIONS_FILE")
  LISTEN_PORT=$(jq -r '(.listen_port // .options.listen_port) // 58090' "$OPTIONS_FILE")
  SECURE_ON=$(jq -r '(.secure_on // .options.secure_on) // "aabbccddeeff"' "$OPTIONS_FILE")
  # allowed_hosts: accept array or string; default to empty string
  ALLOWED_HOSTS=$(jq -r '((.allowed_hosts // .options.allowed_hosts) // []) as $ah
    | if ($ah|type) == "array" then $ah | join(",")
      elif ($ah|type) == "string" then $ah
      else "" end' "$OPTIONS_FILE")

  DNS_TTL=$(jq -r '(.dns_ttl // .options.dns_ttl) // 300' "$OPTIONS_FILE")
  HTTP_API_ENABLED=$(jq -r '(.http_api_enabled // .options.http_api_enabled) // false' "$OPTIONS_FILE")
  API_PORT=$(jq -r '(.api_port // .options.api_port) // 5000' "$OPTIONS_FILE")
else
  WOL_PORT=9
  LISTEN_PORT=58090
  SECURE_ON="aabbccddeeff"
  BROADCAST_IP="255.255.255.255"
  ALLOWED_HOSTS=""
  DNS_TTL=300
  HTTP_API_ENABLED=false
  API_PORT=5000
fi

export WOL_PORT BROADCAST_IP LISTEN_PORT SECURE_ON ALLOWED_HOSTS DNS_TTL HTTP_API_ENABLED API_PORT

exec python3 /usr/src/app/app/wol_forwarder.py
