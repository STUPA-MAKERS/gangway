---
id: "000083"
title: A tempo needs four beats in eight seconds
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_dsp.py:test_tempo_needs_enough_beats"
implementation:
  - gangway/audio/dsp.py
scope:
  - gangway/audio/dsp.py
---

# A tempo needs four beats in eight seconds

The tempo must be 0 if the last 8 s hold fewer than 4 beats.

Test: `tests/test_audio_dsp.py:test_tempo_needs_enough_beats`.
