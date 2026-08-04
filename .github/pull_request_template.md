---
name: "Fix README typos and clarify options"
about: "Fix typos and align README with config.json and run.sh"
title: "Fix README typos and clarify options"
labels: "documentation"
assignees: "erkr"
---

This PR corrects spelling and grammar in README.md and aligns the documented option names with the add-on manifest and entrypoint script.

What was changed:
- Fixed typos (daemon, UDP, undefined, attack, secure_on, the, etc.)
- Updated option names to match config.json and run.sh: `secure_on`, `broadcast_ip`, `listen_port`, `wol_port`
- Added `broadcast_ip` to the example options JSON
- Improved Usage and Testing sections for clarity

No code changes were made.
