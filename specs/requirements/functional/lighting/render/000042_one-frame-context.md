---
id: "000042"
title: All LEDs of a frame get the same time and context
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_animations.py:test_controller_moves_beats_to_the_animation_clock"
implementation:
  - gangway/led_controller.py
scope:
  - gangway/led_controller.py
---

# All LEDs of a frame get the same time and context

The render loop must read the animation time and the `SceneContext` once for each frame. It must
give the same values to the animation for every LED of that frame.

Reason: The animations compute their frame values once. A frame with two times gives a visible
seam.

Test: `tests/test_audio_animations.py:test_controller_moves_beats_to_the_animation_clock`.
