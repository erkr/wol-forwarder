import socket
import logging
import time
from typing import Optional, Dict, Tuple, List, Set
from ha_webhook import send_ha_webhook

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
        known_hosts: Optional[list[dict]] = None,
        host_filtering: bool = False,
        mac_list: Optional[list[dict]] = None,
        mac_filtering: bool = False,
        ha_api_url: str = "",
        http_api_expose: bool = False,
        dns_ttl: int = 300,
        recv_timeout: float = 1.0,
        webhook_id: str = "",
        webhook_sel: str = "forward"
    ):
        """
        Initialize the WoL packet listener.
        
        Args:
            listen_port: UDP port to listen on 
            wol_port: default standard WoL 9 broadcast port
            listen_address: Address to bind to (0.0.0.0 listens on all interfaces)
            secure_on_password: Expected secureOn password (6 bytes) for verification
            known_hosts: Optional list of hostname and their alias pairs (resolved via DNS)
            host_filtering: Use the known hosts list for filtering WoL requests
            mac_list: Optional list of MAC addreses and their alias pairs 
            mac_filtering: Use the MAC list for filtering WoL requests
            dns_ttl: seconds to cache successful DNS results
            recv_timeout: timeout for the receive socket
            webhook_id: optional web_hook id to post reports to 
        """
        self.listen_port = listen_port
        self.listen_address = listen_address
        self.wol_port = wol_port
        self.broadcast_ip = broadcast_ip
        self.secure_on_password = secure_on_password
        self.socket = None
        self.running = False
        self.recv_timeout = recv_timeout
        self.webhook_id = webhook_id
        self.webhook_forward = bool((webhook_sel in ["all","forward"]) and webhook_id)
        self.webhook_reject = bool((webhook_sel in ["all","reject"]) and webhook_id)
        self.ha_api_url = ha_api_url
        self.http_api_expose = http_api_expose

        # allowed hosts and DNS cache
        self.known_hosts = known_hosts or []
        self.host_filtering = host_filtering
        self.dns_ttl = dns_ttl
        # cache entry structure: host -> { 'ips': set(str), 'name': str, 'last_success': float, 'last_attempt': float }
        self._dns_cache: Dict[str, Dict] = {}
        self._retry_interval = 30  # seconds: how often to retry failed/no-result hosts

        # known MAC adresses and filtering, standardised on colons and uppercase
        for dict in mac_list:
            for k,v in dict.items():
                if k == 'mac':
                    dict[k] = v.replace('-',':').upper()
        self.mac_list = mac_list or []
        self.mac_filtering = mac_filtering
        # Packet statistics (thread-safe counters)
        self.packets_received = 0
        self.packets_accepted = 0
        self.packets_rejected = 0
        self.packets_forwarded = 0
        # DNS lookups
        self.dns_lookups = 0
        self.dns_success = 0
        self.dns_age = 0.0

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
            if self.known_hosts:
              logger.debug("Known Hosts list: %s, HOST Filtering=%s", self.known_hosts, self.host_filtering)
            else: 
              logger.debug("No known Hosts list defined")
            if self.mac_list:
              logger.debug("MAC list: %s, MAC Filtering=%s", self.mac_list, self.mac_filtering)
            else: 
              logger.debug("No MAC list defined")
               
            self.listen()
        except PermissionError:
            logger.error("Permission denied: cannot bind to port %d. Try a port >1024 or run as root.", self.listen_port)
        except Exception as e:
            logger.exception("Error starting listener: %s", e)
    
    def stop(self) -> None:
        """Stop listening (idempotent)."""
        # If already stopped (no socket and not running), do nothing
        if not self.running and self.socket is None:
            return

        # Mark as not running and close socket if present
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        logger.info("WoL listener Stopped...")

    
    def listen(self) -> None:
        """Main loop: receive packets and process them."""
        try:
            while self.running:
                try:
                    if self.known_hosts:  # Ensure cache is frequently refreshed 
                        self._refresh_dns_cache_if_needed()
                    if self.running:
                        data, addr = self.socket.recvfrom(1024)
                        self.packets_received += 1
                    if self.running:
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
        
        # Check source against known_hosts (if filtering and list are configured)
        result = self._check_known_hosts(source_ip)
        if not result.get("valid", False):
            logger.warning("Dropping packet from %s:%d — source not allowed", source_ip, source_port)
            msg = f"Dropping packet from {source_ip}:{source_port} — source not allowed"
            logger.warning(msg)
            self.packets_rejected += 1
            if self.webhook_reject:
                send_ha_webhook(self.webhook_id, {"event":"rejected", "message": msg, "rejected": self.packets_rejected, "accepted": self.packets_accepted})
            return
        source_name=result.get("name", source_ip)
        
        # Verify the packet is a valid WOL packet with the expected SecureOn
        result = self.verify_magic_packet(packet_data)
        if not result.get("valid", False):
            error = result.get("error","invalid packet")
            msg = f"Invalid WOL packet from {source_ip}:{source_port} - {error}"
            logger.warning(msg)
            self.packets_rejected += 1
            if self.webhook_reject:
                send_ha_webhook(self.webhook_id, {"event":"rejected", "message": msg, "rejected": self.packets_rejected, "accepted": self.packets_accepted})
            return
        mac_address = result.get('mac','Unknown')
        
        mac_name = mac_address # default if not in list
        if self.mac_list:
            found = False
            for element in self.mac_list:
                if element.get('mac',None) == mac_address: 
                    mac_name = element.get('name',mac_address)
                    logger.debug("WOL packet found in mac list: %s (%s)", mac_address, mac_name)
                    found = True
                    break
            if not found and self.mac_filtering:        
                msg = f"WOL packet reject - MAC {mac_address} not in allowed mac list"
                logger.warning(msg)
                self.packets_rejected += 1
                if self.webhook_reject:
                   send_ha_webhook(self.webhook_id, {"event":"rejected", "message": msg, "rejected": self.packets_rejected, "accepted": self.packets_accepted})
                return
            
        # Log successful packet
        self.packets_accepted += 1
        logger.info("Valid WoL packet for Target %s received from %s", mac_name, source_name)
        if self.webhook_forward:
            send_ha_webhook(self.webhook_id, {"event":"forwarded", "source_ip": source_ip, "source_name": source_name, "mac_address": mac_address, "mac_name": mac_name })
        # Forward the packet without SecureOn suffix 
        self.send_magic_packet(result["magic_packet"])
    
    def send_magic_packet(self, magic_packet: bytes) -> None:
        """Send the stripped 102-byte magic packet as a UDP broadcast."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, (self.broadcast_ip, self.wol_port))
            self.packets_forwarded += 1
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
        oldest = 0.0
        nr_lookups = self.dns_lookups

        for known_host in self.known_hosts:
            host = known_host.get('host')
            name = known_host.get('name')
            entry = self._dns_cache.get(host)
            if entry is None:
                entry = {'ips': set(), 'name': 'n/a', 'last_success': 0.0, 'last_attempt': 0.0}

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
                    self.dns_lookups += 1
                    if ips:
                        entry['ips'] = ips
                        entry['name'] = name
                        entry['last_success'] = now
                        logger.debug("Resolved %s -> %s (%s)", host, ips, name)
                        self.dns_success += 1
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
                
            # update age info
            oldest = max(now - entry['last_success'], oldest)
            
        self.dns_age = oldest
        if ( self.dns_lookups > nr_lookups):
            logger.debug("DNS refresh Stats: oldest %1.1f sec, #lookups: %d, #success %d", self.dns_age, self.dns_lookups, self.dns_success)

    def _check_known_hosts(self, source_ip: str) -> Dict:
        # allow all when no known_hosts configured
        if not self.known_hosts:
            return {"valid": True, "name": source_ip}

        # Check against cached IPs
        for host, entry in self._dns_cache.items():
            if source_ip in entry.get('ips', set()):
                name = entry.get('name', source_ip)
                logger.debug("Source %s matched allowed host %s (%s)", source_ip, host, name)
                return {"valid": True, "name": name}
                
        # No match
        if self.host_filtering:
            logger.debug("Source %s is not in allowed hosts list", source_ip)
            return {"valid": False}
        # no filtering
        return {"valid": True, "name": source_ip}

    def get_config(self) -> Dict:
        """Return current listener config."""
        return {
            'running': self.running,
            'loglevel': logging.getLevelName(logger.getEffectiveLevel()),
            'listen_address': self.listen_address,
            'listen_port': self.listen_port,
            'wol_port': self.wol_port,
            'broadcast_ip': self.broadcast_ip,
            'known_hosts': self.known_hosts,
            'host_filtering': self.host_filtering,
            'mac_list': self.mac_list,
            'mac_filtering': self.mac_filtering,
            'http_api_expose': self.http_api_expose,
            'webhook_reporting': {
               'ha_api_url': self.ha_api_url,
               'forwarded': self.webhook_forward,
               'rejected': self.webhook_reject
            }
        }
        
    def get_stats(self) -> Dict:
        """Return current listener statistics."""
        return {
            'running': self.running,
            'packets': {
                'received': self.packets_received,
                'accepted': self.packets_accepted,
                'rejected': self.packets_rejected,
                'forwarded': self.packets_forwarded,
            },
        }

    def get_dns_cache(self) -> Dict:
        """Return current listener dns cache."""
        return {
            'running': self.running,
            'dns_cache': {
                host: {
                    'ips': sorted(list(entry.get('ips', set()))),
                    'name': entry.get('name', ''),
                    'resolved': bool(entry.get('ips')),
                    'last_success': round(entry.get('last_success', 0),3),
                    'last_attempt': round(entry.get('last_attempt', 0),3),
                }
                for host, entry in self._dns_cache.items()
            },
            'statistics': {
                'lookups': self.dns_lookups,
                'success': self.dns_success,
                'oldest': round(self.dns_age,1),
           },
        }

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
        mac_bytes = packet_data[6:12]
        for i in range(1, 16):
            if packet_data[6 + i*6:6 + (i+1)*6] != mac_bytes:
                return {"valid": False, "error": "Not a valid WoL packet - MAC address mismatch in repetitions"}
        

        packet_password = packet_data[102:108]
        if packet_password != self.secure_on_password:
            return {"valid": False, "error": "WoL Packet rejected - invalid secureOn"}

        # magic packet to send is the first 102 bytes (sync + 16*mac)
        magic_packet = packet_data[:102]
        mac_address = mac_bytes.hex(':').upper()
        return { "valid": True, "magic_packet": magic_packet, "mac": mac_address }
