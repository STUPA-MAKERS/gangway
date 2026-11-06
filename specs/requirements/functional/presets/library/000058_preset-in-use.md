---
id: "000058"
title: A preset in use cannot be deleted
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A preset in use cannot be deleted

`DELETE /api/presets/{name}` must refuse with 400 if the active config or a different preset
uses the preset. A missing preset must give 404.

Reason: A deleted preset in use would turn the LEDs off.

Test: Review.
