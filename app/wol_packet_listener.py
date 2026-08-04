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




class WoLPacketListener:
    """Listen for Wake-on-LAN magical packets and verify them."""
    
    def __init__(
        self,
        listen_port: int = 58090,
        listen_address: str = "0.0.0.0",
        wol_port: int = 9,
        broadcast_ip: str = '255.255.255.255'
        secure_on_password: bytes = "aabbccddeeff"
    ):
        """
        Initialize the WoL packet listener.
        
        Args:
            listen_port: UDP port to listen on 
            wol_port: default standard WoL 9 broadcast port
            listen_address: Address to bind to (0.0.0.0 listens on all interfaces)
            secure_on_password: Expected secureOn password (6 bytes) for verification
        """
        self.listen_port = listen_port
        self.wol_port = wol_port
        self.broadcast_ip = broadcast_ip
        self.listen_address = listen_address
        self.secure_on_password = secure_on_password
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
            pass
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
        result = verify_magic_packet(packet_data)
        
        if not result["valid"]:
            logger.warning(f"Invalid packet from {source_ip}:{source_port} - {result['error']}")
            return
                
        # Log successful packet
        logger.info( f"WoL packet with valid SecureOn password received from {source_ip}:{source_port}" )       
        # Forward the packet without SecureOn suffix 
        self.send_magic_packet(result["magic_packet"])
    
    def send_magic_packet(magic_packet: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, (self.broadcast_ip, self.wol_port))
        finally:
            sock.close()

    def verify_magic_packet(packet_data: bytes) -> Dict:
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
            dict: validation status and error or magical packet 
        """
        
        # Verify WoL with SecureOn packet size 
        if len(packet_data) != 108:
            return {"valid": False, "Warning": "Not a valid WoL packet - size doesn't match"}
        
        # Verify synchronization stream (first 6 bytes should be 0xFF)
        sync_stream = packet_data[:6]
        if sync_stream != b'\xff' * 6:
            return {"valid": False, "Warning": "Not a valid WoL packet - invalid synchronization stream"}
        
        # Extract and verify MAC address (repeated 16 times)
        mac_address = packet_data[6:12]
        for i in range(1, 16):
            if packet_data[6 + i*6:6 + (i+1)*6] != mac_address:
                return {"valid": False, "Warning": "Not a valid WoL packet - MAC address mismatch in repetitions"}
        

        packet_password = packet_data[102:108]
        if packet_password != self.secure_on_password:
            return {"valid": False, "Warning": "WoL Packet without valid secureOn "}
        
        return { "valid": True, "magic_packet": packet_data[:102] }



