---
id: "000082"
title: The bass gain scales only the bass bands
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_dsp.py:test_bass_gain_only_scales_the_bass_bands"
  - "tests/test_audio_dsp.py:test_bass_gain_lifts_quiet_bass_above_the_floor"
implementation:
  - gangway/audio/dsp.py
scope:
  - gangway/audio/dsp.py
---

# The bass gain scales only the bass bands

`bass_gain` must multiply the bass bands before the analysis. It must not change the mid and the
treble bands.

Reason: The USB microphone picks up little bass.

Test: `tests/test_audio_dsp.py:test_bass_gain_only_scales_the_bass_bands`,
`tests/test_audio_dsp.py:test_bass_gain_lifts_quiet_bass_above_the_floor`.
