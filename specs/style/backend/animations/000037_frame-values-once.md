---
id: "000037"
title: An audio animation computes frame values once
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/animations/audio/_frame.py
scope:
  - gangway/animations/audio
---

# An audio animation computes frame values once

An audio animation must compute the values of a frame once with `per_frame` from
`gangway/animations/audio/_frame.py`. It must not compute them again for each LED.

Reason: The closure of an animation runs once for each LED. The installation has 216 LEDs.

Test: Review.
