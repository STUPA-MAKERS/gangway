---
id: "000059"
title: The config API changes only the animation
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_api.py:test_update_config"
  - "tests/test_api.py:test_update_config_keeps_the_audio_section"
implementation:
  - gangway/api/config.py
scope:
  - gangway/api/config.py
---

# The config API changes only the animation

`PUT /api/config/` must save only the `animation` section. It must keep `projection`, `leds`,
`strips` and `audio` as the file has them.

Reason: The web UI must not change the hardware layout or the microphone.

Test: `tests/test_api.py:test_update_config`,
`tests/test_api.py:test_update_config_keeps_the_audio_section`.
