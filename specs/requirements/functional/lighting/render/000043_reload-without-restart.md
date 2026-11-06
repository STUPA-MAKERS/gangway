---
id: "000043"
title: A new animation applies without a restart
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_api.py:test_update_config"
implementation:
  - gangway/api/config.py
  - gangway/api/presets.py
  - gangway/led_controller.py
scope:
  - gangway/api
  - gangway/led_controller.py
---

# A new animation applies without a restart

A change of the animation through the API must reload the config and call
`LEDController.reload_config`. The next frame must show the new animation.

Test: `tests/test_api.py:test_update_config`.
