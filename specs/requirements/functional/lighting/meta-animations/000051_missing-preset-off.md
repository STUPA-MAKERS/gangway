---
id: "000051"
title: A missing or recursive preset turns the LEDs off
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets.py:test_preset_reads_presets_next_to_config"
  - "tests/test_presets.py:test_missing_preset_turns_leds_off"
implementation:
  - gangway/animations/meta/preset.py
scope:
  - gangway/animations/meta/preset.py
---

# A missing or recursive preset turns the LEDs off

The `preset` animation must read `presets/<name>.yaml` next to the config file. A missing file,
an empty file or a preset that contains itself must give the color off.

Reason: A recursive preset must not stop the config load.

Test: `tests/test_presets.py:test_preset_reads_presets_next_to_config`,
`tests/test_presets.py:test_missing_preset_turns_leds_off`.
