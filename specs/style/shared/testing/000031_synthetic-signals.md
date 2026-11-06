---
id: "000031"
title: The sound analysis is tested with synthetic signals
kind: style
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_beats.py:test_steady_kicks_give_a_steady_grid"
  - "tests/test_audio_dsp.py:test_bass_tone_raises_bass_not_treble"
implementation:
  - tests/test_audio_dsp.py
  - tests/test_audio_beats.py
scope:
  - gangway/audio
  - tests
---

# The sound analysis is tested with synthetic signals

The tests of `gangway/audio/dsp.py` and `gangway/audio/beats.py` must use generated signals.
They must not open a sound device. A test signal for the beat tracker must contain a little
noise.

Reason: CI has no microphone. aubio gives no beat in a hop of digital silence.

Test: `tests/test_audio_beats.py:test_steady_kicks_give_a_steady_grid`,
`tests/test_audio_dsp.py:test_bass_tone_raises_bass_not_treble`.
