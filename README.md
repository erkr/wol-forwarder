# WOL Forwarder Home Assistant Add-on

This add-on provides a small deamon to forward Wake-on-LAN magic packets on your LAN. 

The use case to be solved in more detail:
- enable WOL remotely from the internet is a 'secure' way. 
- many routers deliberately don't support forwarding broadcasts, only to a specific IP/port on the LAN.
- broadcasts can be used as a DDOS attac, So opening the known WOL port 7 or 9 is not great either
- When forwarding. it is not nice if that can be done unsolicited

 What WOL forwarder offers:
  - The router forwards UDP's from any undefiend port (typically above 50000) to this WOL forwarder deamon
  - The deamon will check if the incomming UDP packet to be a valid WOL packet with a matching password (SecureON)
  - Only valid packets are broadcasted on port 9 in hte local network (without the SecureOn)
There are numerous WOL apps that can send magical packets with a SecureOn password. Also the Home assistant WOL integration can do that.
 
Usage
1. Install this add-on (from this repository branch) in Home Assistant Supervisor.
2. Configure options in the Supervisor add-on UI:
   - wol_port: UDP port to send magic packets to (default 9)
   - listen_port: Port for receiving UDP's forwarded by your router (default 58090)
   - secore_on: a string of exactly 6 hex values (12 bytes, default "aabbccddeeff")


Example options.json
{
  "wol_port": 9,
  "listen_port": 58090,
  "secure_on": "aabbccddeeff"
}

Notes
- Host network mode is needed, so broadcast packets reach the LAN.
