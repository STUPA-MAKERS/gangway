---
id: "000086"
title: The audio data is silent without a capture
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_api.py:test_audio_data_without_capture"
implementation:
  - gangway/api/data.py
scope:
  - gangway/api/data.py
---

# The audio data is silent without a capture

Without a capture, `GET /api/data/audio` must give `capturing: false`, 0 for each value and
`since_beat: null`.

Test: `tests/test_api.py:test_audio_data_without_capture`.
