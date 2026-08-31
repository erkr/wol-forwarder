# Changelog DEV version

## v1.2.2 

Improvements:
- Extended statistics with WoL packet forward failed count and a DNS Healthy flag
- Added basic statistics to `forwarded` webhook payload, equal to `rejected` (to facilitate webhook based template sensors)
- Added a `statistics` Webhook (Posts when started or issues occured)

Breaking:
- Changed `stats` endpoint; 
   - removed `received` packets counter 
   - replaced `forwarded` counter by a `failed` counter 
- Config option `webhook_sel` is removed. If `webhook_id` is configured all events are reported

