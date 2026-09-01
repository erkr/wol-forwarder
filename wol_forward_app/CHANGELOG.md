# Changelog

## v1.2.2 

Improvements:
- Extended statistics with WoL packet `failed` count and a `DNS Healthy` flag
- Added statistics to `forwarded` webhook payload (equal to `rejected` to facilitate webhook based template sensors)
- Added a `statistics` Webhook (Posts when either started or issues occured)
- Added a `reset` endpoint to clear specified counters
- Added more triggered template sensor examples

Breaking:
- Changed content of the `stats` endpoint; 
   - removed `received` packets counter 
   - replaced `forwarded` counter by a `failed` counter 
- Config option `webhook_sel` is removed. If a `webhook_id` is configured all events will be reported

Updates:
- Updated container base image to python:3.14-slim
- Updated library versions in requirements.txt

## v1.2.1

Improvements:
- Version tag passed to image and logged while starting
- Revised installation instructions in the readme using standard badges and redirects
- Added oldest successfull lookup to DNS statistics
- Added examples

Breaking:
- None

## v1.2.0 

Improvements:
- Security: added AppArmor as an extra protection layer
- Added parmeters ha_api_url and loglevel to config endpoint data

Changes HTTP Server:
- Replaced http_api_enabled option by http_api_expose option. 
- The HTTP server runs always now, but listens to the internal HA network only by default.
- In normal operation the HTTP API logging (Flask/Werkzeug is chatty on INFO) is adjusted to WARNING when the selected logger level is INFO 

Maintenance:
- Updated container base image to python:3.12-slim

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
