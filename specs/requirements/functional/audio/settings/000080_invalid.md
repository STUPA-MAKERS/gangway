---
id: "000080"
title: An invalid audio setting is refused
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_capture.py:test_parse_settings_rejects_bad_values"
implementation:
  - gangway/audio/settings.py
scope:
  - gangway/audio/settings.py
---

# An invalid audio setting is refused

An unknown key must raise `ValueError`. A value of the wrong type, a `sample_rate` or a
`block_size` below 1, or a negative `noise_floor` or `bass_gain` must raise `TypeError`. A
boolean must not count as a number.

Test: `tests/test_audio_capture.py:test_parse_settings_rejects_bad_values`.
