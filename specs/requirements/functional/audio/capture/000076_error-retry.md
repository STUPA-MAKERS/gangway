---
id: "000076"
title: A capture error gives silence and a retry
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_capture.py:test_capture_publishes_beats_and_survives_errors"
implementation:
  - gangway/audio/capture.py
scope:
  - gangway/audio/capture.py
---

# A capture error gives silence and a retry

On an error of the device, the capture must log one warning, publish `SILENT_AUDIO` and try
again after 5 s.

Reason: A missing microphone must not stop the lights.

Test: `tests/test_audio_capture.py:test_capture_publishes_beats_and_survives_errors`.
