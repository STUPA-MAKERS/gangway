---
id: "000054"
title: A save without a body stores the active animation
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A save without a body stores the active animation

`POST /api/presets/{name}` without a body must store the animation of the config file. With a
body, it must store the animation of the body.

Test: Review.
