# Changelog DEV version

## v1.3.1b1

Improvements:
- replaced `dns_success` by a resettable counter `dns_failed`
- replaced reset option `packets_forwarded` (doing nothing) by reset `dns_failed` (new)
- added (hidden) `wol_repeats` config option (default 2, range 1-5)

Breaking:

Updates:
