# Changelog DEV version

## v1.3.0

Improvements:
- Extended statistics with WoL packet `failed` count and a `DNS Healthy` flag
- Added statistics to `forwarded` webhook payload (equal to `rejected` to facilitate webhook based template sensors)
- Added a `statistics` Webhook (Posts when either started, counter cleared or DNS issues occured)
- Added a `reset` endpoint to clear the specified counters
- Added  triggered template sensor examples

Breaking:
- Changed content of the `stats` endpoint; 
   - removed `received` packets counter 
   - replaced `forwarded` counter by a `failed` counter 
- Config option `webhook_sel` is removed. If a `webhook_id` is configured all events will be reported

Updates:
- Updated container base image to python:3.14-slim
- Updated library versions in requirements.txt