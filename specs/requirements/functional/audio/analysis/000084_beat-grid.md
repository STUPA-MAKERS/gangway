---
id: "000084"
title: Beats lie on a tempo grid
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_beats.py:test_a_kick_off_the_grid_gives_no_beat"
  - "tests/test_audio_beats.py:test_a_missing_kick_still_gives_a_beat"
implementation:
  - gangway/audio/beats.py
scope:
  - gangway/audio/beats.py
---

# Beats lie on a tempo grid

The beat tracker must put the beats on a tempo grid. A kick off the grid must not give a beat. A
missing kick on the grid must still give a beat.

Test: `tests/test_audio_beats.py:test_a_kick_off_the_grid_gives_no_beat`,
`tests/test_audio_beats.py:test_a_missing_kick_still_gives_a_beat`.
