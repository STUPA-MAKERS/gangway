---
id: "000060"
title: A config file without an audio section keeps none
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_api.py:test_update_config_keeps_the_audio_section"
implementation:
  - gangway/api/config.py
scope:
  - gangway/api/config.py
---

# A config file without an audio section keeps none

If the config file has no `audio` section, `PUT /api/config/` must not write one.

Reason: Without the section the defaults of the application apply, also after an update.

Test: `tests/test_api.py:test_update_config_keeps_the_audio_section`.
