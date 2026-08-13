# Changelog

## v1.1.1
Improvements:
- Added optional config option for webhook reports (all, forwarded, rejected, disabled)

## v1.1.0
Improvements:
- Continuously refresh DNS cache while waiting for WoL packets
- Changed default for HTTP API port to 58080 to avoid collisions with other Flask based apps

Breaking:
- Revised endpoints. 
- Removed shutdown endpoint
