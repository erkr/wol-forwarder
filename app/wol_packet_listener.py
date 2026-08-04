import socket
import logging
import time
from typing import Optional, Dict, Tuple, List, Set

# Configure logging (the main module configures root logging; keep this basic)
logger = logging.getLogger(__name__)




class WoLPacketListener:
    """
    Listen for Wake-on-LAN magic packets, optionally verify SecureOn password,
    and forward the packet (without SecureOn suffix) as a broadcast on the LAN.
    """
    
    def __init__(
        self,
        listen_port: int = 58090,
        listen_address: str = "0.0.0.0",
        wol_port: int = 9,
        broadcast_ip: str = "255.255.255.255",
        secure_on_password: bytes = b"",
        allowed_hosts: Optional[List[str]] = None,
        dns_ttl: int = 300,
        recv_timeout: float = 1.0,
    ):
        """
        Initialize the WoL packet listener.
        
        Args:
            listen_port: UDP port to listen on 
            wol_port: default standard WoL 9 broadcast port
            listen_address: Address to bind to (0.0.0.0 listens on all interfaces)
            secure_on_password: Expected secureOn password (6 bytes) for verification
            allowed_hosts: Optional list of hostnames to allow (resolved via DNS)
            dns_ttl: seconds to cache successful DNS results
        """
        self.listen_port = listen_port
        self.listen_address = listen_address
        self.wol_port = wol_port
        self.broadcast_ip = broadcast_ip
        self.secure_on_password = secure_on_password
        self.socket = None
        self.running = False
        self.recv_timeout = recv_timeout

        # allowed hosts and DNS cache
        self.allowed_hosts = allowed_hosts or []
        self.dns_ttl = dns_ttl
        # cache entry structure: host -> { 'ips': set(str), 'last_success': float, 'last_attempt': float }
        self._dns_cache: Dict[str, Dict] = {}
        self._retry_interval = 30  # seconds: how often to retry failed/no-result hosts

    def start(self) -> None:
        """Start the listener (blocking until stop() is called)."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Allow rebinding; on some platforms this is required for quick restarts
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # set a small timeout so we can respond to stop() quickly
            self.socket.settimeout(self.recv_timeout)
            self.socket.bind((self.listen_address, self.listen_port))
            
            self.running = True
            logger.info("WoL listener started on %s:%d", self.listen_address, self.listen_port)
            
            self.listen()
        except PermissionError:
            logger.error("Permission denied: cannot bind to port %d. Try a port >1024 or run as root.", self.listen_port)
        except Exception as e:
            logger.exception("Error starting listener: %s", e)
    
    def stop(self) -> None:
        """Stop listening."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        logger.info("WoL listener stopped")
    
    def listen(self) -> None:
        """Main loop: receive packets and process them."""
        logger.info("Listening for WOL packets...")
        try:
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    self.process_packet(data, addr)
                except socket.timeout:
                    continue
                except OSError as e:
                    # socket closed or other network error
                    if not self.running:
                        break
                    logger.warning("Socket error: %s", e)
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
        
        # Check source against allowed_hosts (if configured)
        if not self._is_source_allowed(source_ip):
            logger.info("WoL packet with valid SecureOn password received from %s:%d", source_ip, source_port)
            return
        
        # Verify the packet
        result = self.verify_magic_packet(packet_data)
        if not result.get("valid", False):
            logger.warning("Invalid WOL packet from %s:%d - %s", source_ip, source_port, result.get("error"))
            return
                
        # Log successful packet
        logger.info( f"WoL packet with valid SecureOn password received from {source_ip}:{source_port}" )       
        # Forward the packet without SecureOn suffix 
        self.send_magic_packet(result["magic_packet"])
    
    def send_magic_packet(self, magic_packet: bytes) -> None:
        """Send the stripped 102-byte magic packet as a UDP broadcast."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, (self.broadcast_ip, self.wol_port))
            logger.debug("Sent magic packet (%d bytes) to %s:%d", len(magic_packet), self.broadcast_ip, self.wol_port)
        except Exception:
            logger.exception("Failed to send magic packet to %s:%d", self.broadcast_ip, self.wol_port)
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _resolve_host(self, hostname: str) -> Set[str]:
        """Resolve hostname to a set of IP strings (IPv4/IPv6)."""
        try:
            infos = socket.getaddrinfo(hostname, None)
            ips = {ai[4][0] for ai in infos}
            return ips
        except Exception as e:
            logger.debug("DNS resolution failed for %s: %s", hostname, e)
            return set()

    def _refresh_dns_cache_if_needed(self):
        now = time.time()
        for host in self.allowed_hosts:
            entry = self._dns_cache.get(host)
            if entry is None:
                entry = {'ips': set(), 'last_success': 0.0, 'last_attempt': 0.0}

            need_try = False
            if entry['ips']:
                # have previous success — try refresh only if last_success older than ttl
                if now - entry['last_success'] > self.dns_ttl:
                    need_try = True
            else:
                # never succeeded — retry only if enough time passed since last attempt
                if now - entry['last_attempt'] > self._retry_interval:
                    need_try = True

            if need_try:
                entry['last_attempt'] = now
                try:
                    ips = self._resolve_host(host)
                    if ips:
                        entry['ips'] = ips
                        entry['last_success'] = now
                        logger.debug("Resolved %s -> %s", host, ips)
                    else:
                        # resolution returned empty set; keep previous ips if any
                        if entry['ips']:
                            logger.warning("DNS refresh for %s returned empty; keeping previous IPs %s", host, entry['ips'])
                        else:
                            logger.warning("DNS resolution for %s returned empty (no previous IPs)", host)
                except Exception as e:
                    if entry['ips']:
                        logger.warning("DNS refresh failed for %s, keeping previous IPs %s: %s", host, entry['ips'], e)
                    else:
                        logger.warning("DNS resolution failed for %s (no previous IPs): %s", host, e)
                self._dns_cache[host] = entry

    def _is_source_allowed(self, source_ip: str) -> bool:
        # Backwards compatible: allow all when no allowed_hosts configured
        if not self.allowed_hosts:
            return True

        # Ensure cache is refreshed as needed
        self._refresh_dns_cache_if_needed()

        # Check against cached IPs
        for host, entry in self._dns_cache.items():
            if source_ip in entry.get('ips', set()):
                logger.debug("Source %s matched allowed host %s", source_ip, host)
                return True

        # No match
        logger.info("Source %s is not in allowed hosts (%s)", source_ip, self.allowed_hosts)
        return False

    def verify_magic_packet(self, packet_data: bytes) -> Dict:
        """
        Receives and verifies a Wake-on-LAN (WoL) magical packet.
        
        A magical packet with SecureOn is 108 bytes:
        - First 6 bytes: 0xFF (synchronization stream)
        - Next 96 bytes: MAC address repeated 16 times
        - Last 6+ bytes: mandatory to additionally pass a secureOn password
        
        Args:
            packet_data: Raw packet bytes received
            secure_on_password: Expected secureOn password (6 bytes), if required
        
        Returns:
            dict: validation status and error or magical packet 
        """
        
        # Verify WoL with SecureOn packet size 
        if len(packet_data) != 108:
            return {"valid": False, "error": "Not a valid WoL packet - size doesn't match"}
        
        # Verify synchronization stream (first 6 bytes should be 0xFF)
        sync_stream = packet_data[:6]
        if sync_stream != b'\xff' * 6:
            return {"valid": False, "error": "Not a valid WoL packet - invalid synchronization stream"}
        
        # Extract and verify MAC address (repeated 16 times)
        mac_address = packet_data[6:12]
        for i in range(1, 16):
            if packet_data[6 + i*6:6 + (i+1)*6] != mac_address:
                return {"valid": False, "error": "Not a valid WoL packet - MAC address mismatch in repetitions"}
        

        packet_password = packet_data[102:108]
        if packet_password != self.secure_on_password:
            return {"valid": False, "error": "WoL Packet without valid secureOn "}

        # magic packet to send is the first 102 bytes (sync + 16*mac)
        magic_packet = packet_data[:102]
        return { "valid": True, "error": None, "magic_packet": magic_packet }
