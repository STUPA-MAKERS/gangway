---
id: "000056"
title: A rename updates every reference
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A rename updates every reference

`POST /api/presets/{name}/rename` must change the references to the preset in the config file
and in all presets. A new name that exists must give 400. A missing preset must give 404. If the
config cannot change, the file must get its old name again.

Reason: A reference to the old name would turn the LEDs off.

Test: Review.
