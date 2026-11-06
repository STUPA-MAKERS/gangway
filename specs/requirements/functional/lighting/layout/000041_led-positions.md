---
id: "000041"
title: LED positions follow the strips
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_config.py:test_load_config"
  - "tests/test_helpers.py:test_interpolate_points"
implementation:
  - gangway/config.py
  - gangway/helpers.py
scope:
  - gangway/config.py
  - config.yaml
---

# LED positions follow the strips

Each item of `strips` must give `len` LEDs. The LED number `i` of a strip must have the index
`index + i` and a floor position on the line from `start` to `end`. `leds.offset_x` and
`leds.offset_y` must move all strips.

Reason: The animations compute the color of an LED from its floor position.

Test: `tests/test_config.py:test_load_config`, `tests/test_helpers.py:test_interpolate_points`.
