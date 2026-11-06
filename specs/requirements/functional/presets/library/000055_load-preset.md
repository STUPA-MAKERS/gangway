---
id: "000055"
title: A loaded preset becomes the active animation
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A loaded preset becomes the active animation

`POST /api/presets/{name}/load` must write the animation of the preset into the config file and
reload the controller. A missing preset must give 404.

Test: `frontend/src/app/pages/presets/presets.page.spec.ts` and review.
