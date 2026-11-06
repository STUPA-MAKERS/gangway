---
id: "000078"
title: The capture prefers the direct hardware device
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_capture.py:test_find_device_prefers_the_direct_hardware_device"
implementation:
  - gangway/audio/capture.py
scope:
  - gangway/audio/capture.py
---

# The capture prefers the direct hardware device

A device name must match every input device whose name contains it, with any case. An ALSA `hw:`
device must come before the other matches.

Reason: The other ALSA devices resample or mix in software.

Test: `tests/test_audio_capture.py:test_find_device_prefers_the_direct_hardware_device`.
