---
id: "000081"
title: Sound below the noise floor is silence
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_dsp.py:test_quiet_noise_below_the_floor_stays_silent"
  - "tests/test_audio_dsp.py:test_silence_gives_no_level_and_no_beats"
implementation:
  - gangway/audio/dsp.py
scope:
  - gangway/audio/dsp.py
---

# Sound below the noise floor is silence

A block with an RMS value below `noise_floor` must give level 0 and no beat.

Test: `tests/test_audio_dsp.py:test_quiet_noise_below_the_floor_stays_silent`,
`tests/test_audio_dsp.py:test_silence_gives_no_level_and_no_beats`.
