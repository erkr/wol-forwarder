#!/usr/bin/env python3
"""
Simple WOL forwarder for enabling remote WoL support. 
The router forwards external UPD packets to this app.
Only WoL packets with the correct SecureOn password are broadcasted on the local LAN

Reads options from /data/options.json when available (Supervisor).
"""

#import json
import os
#import socket
import struct
import sys
import logging
from typing import Optional, Dict, Tuple
from wol_packet_listener import WoLPacketListener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Defaults (can be overridden by /data/options.json or env vars set by run.sh)
WOL_PORT = int(os.environ.get('WOL_PORT', 9))
BROADCAST_IP = os.environ.get('BROADCAST_IP', '255.255.255.255')
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', 58090))
SECURE_ON = os.environ.get('SECURE_ON', 'aabbccddeeff')
ALLOWED_IPS = None



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
    
    # Create and start listener
    listener = WoLPacketListener(
        listen_port=LISTEN_PORT,
        listen_address="0.0.0.0",
        wol_port=WOL_PORT,
        broadcast_ip=BROADCAST_IP,
        secure_on_password=secure_on_password
    )
    
    
    try:
        listener.start()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()



if __name__ == "__main__":
    main()

