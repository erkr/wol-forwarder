#!/usr/bin/env bash
# Entrypoint for the WOL Forwarder add-on
set -e

# Supervisor provides options in /data/options.json
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
  WOL_PORT=$(jq -r '.wol_port // 9' $OPTIONS_FILE)
  HTTP_PORT=$(jq -r '.http_port // 8090' $OPTIONS_FILE)
  LOG_TO_FILE=$(jq -r '.log_to_file // false' $OPTIONS_FILE)
  LOG_FILE=$(jq -r '.log_file // "/config/wol-forwarder.log"' $OPTIONS_FILE)
else
  WOL_PORT=9
  HTTP_PORT=8090
  LOG_TO_FILE=false
  LOG_FILE="/config/wol-forwarder.log"
fi

export WOL_PORT HTTP_PORT LOG_TO_FILE LOG_FILE

exec python3 /usr/src/app/app/wol_forwarder.py
