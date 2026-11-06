---
id: "000044"
title: The frame rate is the mean of the last 100 frames
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/led_controller.py
  - gangway/api/data.py
scope:
  - gangway/led_controller.py
  - gangway/api/data.py
---

# The frame rate is the mean of the last 100 frames

`fps`, `tpf_min`, `tpf_max` and `tpf_avg` must come from the times of the last 100 frames. A
frame time must include the render and the strip update. `GET /api/data/fps` must give the frame
times in milliseconds with two decimals.

Test: Review.
