#!/usr/bin/env python3
"""
Simple WOL forwarder for enabling remote WoL support.
Reads options from /data/options.json when available (Supervisor).
"""

import os
import sys
import signal
import logging
import threading
from typing import List, Optional
from wol_packet_listener import WoLPacketListener
from http_api import create_api_server
import json
from jsonschema import validate
import re

# Configure logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info')
logging.basicConfig(
    level=LOG_LEVEL.upper(),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Defaults (can be overridden by env vars set by run.sh)
WOL_PORT = int(os.environ.get('WOL_PORT', 9))
BROADCAST_IP = os.environ.get('BROADCAST_IP', '255.255.255.255')
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', 58090))
SECURE_ON = os.environ.get('SECURE_ON', 'a1:b2:c3:d4:e5:f6')
HOST_FILTERING = os.environ.get('HOST_FILTERING', 'false').lower() in ('true', '1', 'yes')
KNOWN_HOSTS = os.environ.get('KNOWN_HOSTS', '{}')
MAC_FILTERING = os.environ.get('MAC_FILTERING', 'false').lower() in ('true', '1', 'yes')
MAC_LIST = os.environ.get('MAC_LIST', '{}')
DNS_TTL = int(os.environ.get('DNS_TTL', 300))
HTTP_API_ENABLED = os.environ.get('HTTP_API_ENABLED', 'false').lower() in ('true', '1', 'yes')
API_PORT = int(os.environ.get('API_PORT', 58080))
WEBHOOK_ID = os.environ.get('WEBHOOK_ID', '')
WEBHOOK_SEL = os.environ.get('WEBHOOK_SEL', 'forward')
HA_API_URL = os.environ.get("HA_API_URL", '')


# Global references for cleanup
api_thread: Optional[threading.Thread] = None
api_app = None

def sigterm_handler(_signo, _stack_frame):
    # Raises SystemExit(0) to close gracefully inside dockers:
    sys.exit(0)

def validate_settings():
    # validate SecurOn 
    if not re.match("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",SECURE_ON):
        logger.error("SecureOn not formatted as a MAC-48 address (eg a1:b2:c3:d4:e5:f6)")
        return False

    # validate Broadcast IP
    if not re.match("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$",BROADCAST_IP):
        logger.error("BROADCAST_IP not formatted as valid IP")
        return False

    # validate integer values
    if not 1 <= WOL_PORT <= 65535:
        logger.error("WOL_PORT invalid value %s range:1 - 65535", WOL_PORT)
        return False
    if not 1024 <= LISTEN_PORT <= 65535:
        logger.error("LISTEN_PORT invalid value %s range:1024 - 65535", LISTEN_PORT)
        return False
    if not 1024 <= API_PORT <= 65535:
        logger.error("API_PORT invalid value %s range:1024 - 65535", API_PORT)
        return False
    if not 60 <= DNS_TTL <= 3600:
        logger.error("DNS_TTL invalid value %s range:60 - 3600", DNS_TTL)
        return False
    
    # validate known Host list
    schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string"
                  }
                },
                "required": ["host","name"]
              }
            }
    try:
        instance = json.loads(KNOWN_HOSTS)
        if instance:
            validate(instance=instance, schema=schema)
    except Exception as ex:
        logger.error("Invalid Host List: %s", ex)
        return False
        
    # validate MAC list
    schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                  "mac": {
                    "type": "string",
                    "pattern": "^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
                  },
                  "name": {
                    "type": "string"
                  }
                },
                "required": ["mac","name"]
              }
            }
    try:
        instance = json.loads(MAC_LIST)
        if instance:
            validate(instance=instance, schema=schema)        
    except Exception as ex:
        logger.error("Invalid MAC List: %s", ex)
        return False
        
    # passed all        
    return True

    
def main():
    """Run the WoL packet listener."""
    global api_thread, api_app
    
    # register handler to gracefully close inside dockers
    signal.signal(signal.SIGTERM, sigterm_handler)
    
    logger.info("WoL Forwarder Starting... LogLevel: %s", LOG_LEVEL)
    if not validate_settings():
        logger.error("Invalid settings passed to WoL Forwarder, Abort...")
        return
    
    # Convert hex 48 bit password string to 6 bytes 
    secure_on_password = bytes.fromhex(re.sub('[:-]', '',SECURE_ON))
    
    # Create listener
    listener = WoLPacketListener(
        listen_port=LISTEN_PORT,
        listen_address="0.0.0.0",
        wol_port=WOL_PORT,
        broadcast_ip=BROADCAST_IP,
        secure_on_password=secure_on_password,
        mac_list= json.loads(MAC_LIST),
        mac_filtering=MAC_FILTERING,
        ha_api_url=HA_API_URL,
        known_hosts=json.loads(KNOWN_HOSTS),
        host_filtering=HOST_FILTERING,
        dns_ttl=DNS_TTL,
        webhook_id=WEBHOOK_ID,
        webhook_sel=WEBHOOK_SEL
    )

    # Start HTTP API server if enabled
    if HTTP_API_ENABLED:
        logger.info("Starting HTTP API server on port %d. Use it for testing only!", API_PORT)
        api_app = create_api_server(listener)
        
        # Flask is very chatty with INFO loggings for every GET request (show only for debug level)
        if logger.getEffectiveLevel() == logging.INFO:
            logger.info("Promote HTTP API LogLevel to Warning")
            logging.getLogger("werkzeug").setLevel(logging.WARNING)

        api_thread = threading.Thread(
            target=lambda: api_app.run(host='0.0.0.0', port=API_PORT, threaded=True),
            daemon=True
        )
        api_thread.start()
    else:
        logger.debug("HTTP API server is disabled")

    
    try:
        listener.start()
    except KeyboardInterrupt:
        pass
    finally:
        if api_app is not None:
            logger.info("HTTP API server Stopped")
            # The daemon flag ensures the thread exits when main thread exits
        # Just to be sure:
        listener.stop()
        logger.info("WoL Forwarder Stopped.")


if __name__ == "__main__":
    main()
