---
id: "000058"
title: A preset in use cannot be deleted
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets_api.py:test_delete_refuses_a_preset_of_the_config"
  - "tests/test_presets_api.py:test_delete_refuses_a_preset_of_a_different_preset"
  - "tests/test_presets_api.py:test_delete_removes_an_unused_preset"
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
---

# A preset in use cannot be deleted

`DELETE /api/presets/{name}` must refuse with 400 if the active config or a different preset
uses the preset. A missing preset must give 404.

Reason: A deleted preset in use would turn the LEDs off.

Test: `tests/test_presets_api.py:test_delete_refuses_a_preset_of_the_config`,
`tests/test_presets_api.py:test_delete_refuses_a_preset_of_a_different_preset`,
`tests/test_presets_api.py:test_delete_removes_an_unused_preset`.
