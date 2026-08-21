# Changelog

## v1.2.0 

Improvements:
- added AppArmor as an extra security layer
- added ha_api_url and loglevel to config endpoint data
- removed http_api_enabled from config endpoint data (redundant info when endpoint can be read)
- Adjust http API logging (chatty Flask/Werkzeug) to WARNING when selected logger level is INFO

## v1.1.2 

Improvements:
- added missing config options to the endpoint `/config`
- added statistics for DNS lookups to the endpoint `/dns`

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
