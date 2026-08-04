#!/usr/bin/env python3
"""
Simple WOL forwarder for enabling remote WoL support.
Reads options from /data/options.json when available (Supervisor).
"""

import os
import logging
import threading
from typing import List
from wol_packet_listener import WoLPacketListener
from http_api import create_api_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Defaults (can be overridden by env vars set by run.sh)
WOL_PORT = int(os.environ.get('WOL_PORT', 9))
BROADCAST_IP = os.environ.get('BROADCAST_IP', '255.255.255.255')
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', 58090))
SECURE_ON = os.environ.get('SECURE_ON', 'aabbccddeeff')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '')  # comma-separated
DNS_TTL = int(os.environ.get('DNS_TTL', 300))
HTTP_API_ENABLED = os.environ.get('HTTP_API_ENABLED', 'false').lower() in ('true', '1', 'yes')
API_PORT = int(os.environ.get('API_PORT', 5000))

# parse allowed hosts into list
allowed_hosts_list: List[str] = [h for h in ALLOWED_HOSTS.split(',') if h]


def main():
    """Run the WoL packet listener."""
    # Convert hex password string to bytes if provided
    secure_on_password = None
    try:
        secure_on_password = bytes.fromhex(SECURE_ON)
        if len(secure_on_password) != 6:
            logger.error("SecureOn password must be exactly 12 hex characters")
            return
    except ValueError:
        logger.error("Invalid hex password format")
        return

    # Create listener
    listener = WoLPacketListener(
        listen_port=LISTEN_PORT,
        listen_address="0.0.0.0",
        wol_port=WOL_PORT,
        broadcast_ip=BROADCAST_IP,
        secure_on_password=secure_on_password,
        allowed_hosts=allowed_hosts_list,
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


if __name__ == "__main__":
    main()
