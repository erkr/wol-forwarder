#!/usr/bin/env bash
# Entrypoint for the WOL Forwarder add-on
set -e

# Supervisor provides options in /data/options.json
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
  WOL_PORT=$(jq -r '.wol_port // 9' $OPTIONS_FILE)
  BROADCAST_IP=$(jq -r '.broadcast_ip // "255.255.255.255"' $OPTIONS_FILE)
  LISTEN_PORT=$(jq -r '.listen_port // 58090' $OPTIONS_FILE)
  SECURE_ON=$(jq -r '.secure_on // "aabbccddeeff"' $OPTIONS_FILE)
  ALLOWED_HOSTS=$(jq -r '.allowed_hosts // [] | join(",")' $OPTIONS_FILE)
  DNS_TTL=$(jq -r '.dns_ttl // 300' $OPTIONS_FILE)
else
  WOL_PORT=9
  LISTEN_PORT=58090
  SECURE_ON="aabbccddeeff"
  BROADCAST_IP="255.255.255.255"
  ALLOWED_HOSTS=""
  DNS_TTL=300
fi

export WOL_PORT BROADCAST_IP LISTEN_PORT SECURE_ON ALLOWED_HOSTS DNS_TTL

exec python3 /usr/src/app/app/wol_forwarder.py
