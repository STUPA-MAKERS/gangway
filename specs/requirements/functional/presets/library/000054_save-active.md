---
id: "000054"
title: A save without a body stores the active animation
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets_api.py:test_save_without_a_body_stores_the_active_animation"
  - "tests/test_presets_api.py:test_save_with_a_body_stores_the_body"
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A save without a body stores the active animation

`POST /api/presets/{name}` without a body must store the animation of the config file. With a
body, it must store the animation of the body.

Test: `tests/test_presets_api.py:test_save_without_a_body_stores_the_active_animation`,
`tests/test_presets_api.py:test_save_with_a_body_stores_the_body`.
