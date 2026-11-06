---
id: "000075"
title: The microphone runs in a child process
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_capture.py:test_process_without_a_device_is_silent_and_stops"
implementation:
  - gangway/audio/process.py
  - main.py
scope:
  - gangway/audio
  - main.py
---

# The microphone runs in a child process

The sound capture must run in a child process that starts with `spawn`. The parent must keep the
latest snapshot that the child sends.

Reason: The render loop holds the GIL. A capture thread in the same process lost half of the
blocks.

Test: `tests/test_audio_capture.py:test_process_without_a_device_is_silent_and_stops`.
