# Changelog DEV version

## v1.3.1

Improvements:
- replaced `dns_success` by a resettable counter `dns_failed`
- replaced reset option `packets_forwarded` (doing nothing) by reset `dns_failed` (new)
- made option `wol_port` optional (default 9 is normally correct)
- added (optional) `wol_repeats` config option (default 2, range 1-5)
- Update Examples triggered template sensors:
  - added DNS sensors (only for v1.3.1+)
  - improved the `total_increasing` sensors (count correctly for a missed webhook events)

Breaking:

Updates:
