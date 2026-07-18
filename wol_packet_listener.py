import socket
import struct
import logging
from typing import Optional, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_magic_packet(packet_data: bytes, secure_on_password: Optional[bytes] = None) -> Dict:
    """
    Receives and verifies a Wake-on-LAN (WoL) magical packet.
    
    A magical packet is 102 bytes:
    - First 6 bytes: 0xFF (synchronization stream)
    - Next 96 bytes: MAC address repeated 16 times
    - Last 6+ bytes: Optional secureOn password
    
    Args:
        packet_data: Raw packet bytes received
        secure_on_password: Expected secureOn password (6 bytes), if required
    
    Returns:
        dict: Packet information and validation status
    """
    
    if len(packet_data) < 102:
        return {"valid": False, "error": "Packet too short"}
    
    # Verify synchronization stream (first 6 bytes should be 0xFF)
    sync_stream = packet_data[:6]
    if sync_stream != b'\xff' * 6:
        return {"valid": False, "error": "Invalid synchronization stream"}
    
    # Extract and verify MAC address (repeated 16 times)
    mac_address = packet_data[6:12]
    for i in range(1, 16):
        if packet_data[6 + i*6:6 + (i+1)*6] != mac_address:
            return {"valid": False, "error": "MAC address mismatch in repetitions"}
    
    # Verify secureOn password if present
    has_secure_on = len(packet_data) > 102
    secure_on_valid = True
    
    if has_secure_on:
        packet_password = packet_data[102:108]
        if secure_on_password:
            if packet_password != secure_on_password:
                secure_on_valid = False
        else:
            return {
                "valid": False,
                "error": "Packet contains secureOn but no password provided for verification"
            }
    
    return {
        "valid": secure_on_valid,
        "mac_address": mac_address.hex(':').upper(),
        "has_secure_on": has_secure_on,
        "secure_on_valid": secure_on_valid,
        "packet_length": len(packet_data)
    }


class WoLPacketListener:
    """Listen for Wake-on-LAN magical packets and verify them."""
    
    def __init__(
        self,
        listen_port: int = 9,
        listen_address: str = "0.0.0.0",
        secure_on_password: Optional[bytes] = None,
        require_secure_on: bool = False
    ):
        """
        Initialize the WoL packet listener.
        
        Args:
            listen_port: UDP port to listen on (default 9 is standard WoL port)
            listen_address: Address to bind to (0.0.0.0 listens on all interfaces)
            secure_on_password: Expected secureOn password (6 bytes) for verification
            require_secure_on: If True, reject packets without secureOn
        """
        self.listen_port = listen_port
        self.listen_address = listen_address
        self.secure_on_password = secure_on_password
        self.require_secure_on = require_secure_on
        self.socket = None
        self.running = False
    
    def start(self) -> None:
        """Start listening for magical packets."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.listen_address, self.listen_port))
            
            self.running = True
            logger.info(f"WoL listener started on {self.listen_address}:{self.listen_port}")
            
            self.listen()
        except PermissionError:
            logger.error(f"Permission denied: Cannot bind to port {self.listen_port}. Try a port > 1024 or run as root.")
        except Exception as e:
            logger.error(f"Error starting listener: {e}")
    
    def stop(self) -> None:
        """Stop listening for packets."""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("WoL listener stopped")
    
    def listen(self) -> None:
        """Listen for and process incoming magical packets."""
        logger.info("Listening for magical packets...")
        
        try:
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    self.process_packet(data, addr)
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            logger.info("Listener interrupted by user")
        finally:
            self.stop()
    
    def process_packet(self, packet_data: bytes, source_addr: Tuple[str, int]) -> None:
        """
        Process a received packet.
        
        Args:
            packet_data: Raw packet bytes
            source_addr: Source IP and port tuple
        """
        source_ip, source_port = source_addr
        
        # Verify the packet
        result = verify_magic_packet(packet_data, self.secure_on_password)
        
        if not result["valid"]:
            logger.warning(f"Invalid packet from {source_ip}:{source_port} - {result['error']}")
            return
        
        # Check if secureOn is required
        if self.require_secure_on and not result["has_secure_on"]:
            logger.warning(f"Rejected packet from {source_ip}:{source_port} - secureOn required but not present")
            return
        
        # Log successful packet
        logger.info(
            f"Valid WoL packet from {source_ip}:{source_port} - "
            f"MAC: {result['mac_address']}, "
            f"SecureOn: {result['has_secure_on']}, "
            f"Length: {result['packet_length']} bytes"
        )
        
        # Process the packet (forward, trigger action, etc.)
        self.handle_valid_packet(result, source_addr)
    
    def handle_valid_packet(self, packet_info: Dict, source_addr: Tuple[str, int]) -> None:
        """
        Handle a valid magical packet.
        Override this method to implement custom behavior (forwarding, logging, etc.).
        
        Args:
            packet_info: Dictionary with packet information
            source_addr: Source IP and port tuple
        """
        mac = packet_info["mac_address"]
        logger.info(f"Handling WoL wake-up request for MAC: {mac}")
        # TODO: Add custom logic here (e.g., forward to target host, trigger action, etc.)


def main():
    """Example usage of the WoL packet listener."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wake-on-LAN Packet Listener")
    parser.add_argument("--port", type=int, default=9, help="UDP port to listen on (default: 9)")
    parser.add_argument("--address", default="0.0.0.0", help="Address to bind to (default: 0.0.0.0)")
    parser.add_argument("--password", help="SecureOn password (hex string, e.g., 'aabbccddeeff')")
    parser.add_argument("--require-secure-on", action="store_true", help="Require secureOn password in packets")
    
    args = parser.parse_args()
    
    # Convert hex password string to bytes if provided
    secure_on_password = None
    if args.password:
        try:
            secure_on_password = bytes.fromhex(args.password)
            if len(secure_on_password) != 6:
                logger.error("SecureOn password must be exactly 6 bytes (12 hex characters)")
                return
        except ValueError:
            logger.error("Invalid hex password format")
            return
    
    # Create and start listener
    listener = WoLPacketListener(
        listen_port=args.port,
        listen_address=args.address,
        secure_on_password=secure_on_password,
        require_secure_on=args.require_secure_on
    )
    
    listener.start()


if __name__ == "__main__":
    main()
