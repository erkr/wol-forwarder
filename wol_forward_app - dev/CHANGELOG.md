# Changelog DEV version

## v1.2.2 

Improvements:
- Added `accepted` and `rejected` counters to `forwarded` webhook payload (to facilitate webhook based template sensors)
- Added DNS statistics to `stats` endpoint
- Added a started Webhook (Posts always when a Webhook ID is configured)

Breaking:
- Small change in `stats` endpoint; removed `received` packets counter and replaced `forwarded` counter by a `failed` counter 

