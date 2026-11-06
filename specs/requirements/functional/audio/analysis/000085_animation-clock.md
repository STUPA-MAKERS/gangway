---
id: "000085"
title: Beat times use the animation clock
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_animations.py:test_controller_moves_beats_to_the_animation_clock"
implementation:
  - gangway/led_controller.py
  - gangway/types/audio_state.py
scope:
  - gangway/led_controller.py
---

# Beat times use the animation clock

The render loop must move the beat times of each snapshot from `time.monotonic` to the animation
time before it gives them to the animations.

Reason: The animation time comes from the wall clock, which can jump on the first NTP sync.

Test: `tests/test_audio_animations.py:test_controller_moves_beats_to_the_animation_clock`.
