# Changelog

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