---
id: "000087"
title: Live data is empty before the controller starts
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/api/data.py
scope:
  - gangway/api/data.py
---

# Live data is empty before the controller starts

Before the LED controller starts, `GET /api/data/objects` must give `[]`, `GET /api/data/leds`
must give `{}` and `GET /api/data/fps` must give 0 for each value.

Test: Review.
