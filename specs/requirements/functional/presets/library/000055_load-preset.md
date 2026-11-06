---
id: "000055"
title: A loaded preset becomes the active animation
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets_api.py:test_load_makes_the_preset_active"
  - "tests/test_presets_api.py:test_load_of_a_missing_preset_gives_404"
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A loaded preset becomes the active animation

`POST /api/presets/{name}/load` must write the animation of the preset into the config file and
reload the controller. A missing preset must give 404.

Test: `tests/test_presets_api.py:test_load_makes_the_preset_active`,
`tests/test_presets_api.py:test_load_of_a_missing_preset_gives_404`,
`frontend/src/app/pages/presets/presets.page.spec.ts`.
