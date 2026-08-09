#!/usr/bin/env python3
"""
Simple WOL forwarder for enabling remote WoL support.
Reads options from /data/options.json when available (Supervisor).
"""

import os
import logging
import threading
from typing import List, Optional
from wol_packet_listener import WoLPacketListener
from http_api import create_api_server
import json
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
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '{}')
MAC_FILTERING = os.environ.get('MAC_FILTERING', 'false').lower() in ('true', '1', 'yes')
MAC_LIST = os.environ.get('MAC_LIST', '{}')
DNS_TTL = int(os.environ.get('DNS_TTL', 300))
HTTP_API_ENABLED = os.environ.get('HTTP_API_ENABLED', 'false').lower() in ('true', '1', 'yes')
API_PORT = int(os.environ.get('API_PORT', 5000))


# Global references for cleanup
api_thread: Optional[threading.Thread] = None
api_app = None


def main():
    """Run the WoL packet listener."""
    global api_thread, api_app
    
    # Convert hex password string to 6 bytes if provided
    try:
        if not re.match("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",SECURE_ON):
            logger.error("SecureOn not formatted as a MAC-48 address (eg a1:b2:c3:d4:e5:f6)")
            return
    except ValueError:
        logger.error("Invalid hex password format")
        return
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
        allowed_hosts=json.loads(ALLOWED_HOSTS),
        dns_ttl=DNS_TTL,
    )

    # Start HTTP API server if enabled
    if HTTP_API_ENABLED:
        logger.info("Starting HTTP API server on port %d", API_PORT)
        api_app = create_api_server(listener)
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
        listener.stop()
        # Gracefully shutdown API if it was started
        if api_app is not None:
            logger.info("Shutting down HTTP API server")
            # The daemon flag ensures the thread exits when main thread exits
            # Add a small wait for graceful shutdown
            if api_thread is not None and api_thread.is_alive():
                api_thread.join(timeout=2)


if __name__ == "__main__":
    main()
