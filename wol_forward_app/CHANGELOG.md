# Changelog

## v1.2.0 (reverted to v1.1.1 due broadcast issues)
Security improvement release:
- The app is no longer fully exposed on your LAN. 
  - Only the listen port for receiving WoL packets.
  - The HTTP API is not exposed (enable only for testing)
- Removed the read only mount of the Home Assistant config folder

breaking:
- Two config options (api_port and listen_port) moved to network settings  

## v1.1.1
Improvements:
- webhook report options configurable(all, forward, reject, disabled), where the default remains forward events.

## v1.1.0
Improvements:
- Continuously refresh DNS cache while waiting for WoL packets
- Changed default for HTTP API port to 58080 to avoid collisions with other Flask based apps

Breaking:
- Revised endpoints. 
- Removed shutdown endpoint

## v1.0.0
Initial stable release
