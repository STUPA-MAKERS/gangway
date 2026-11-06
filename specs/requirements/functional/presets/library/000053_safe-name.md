---
id: "000053"
title: A preset name uses only safe characters
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets_api.py:test_save_refuses_an_unsafe_name"
  - "tests/test_presets_api.py:test_rename_refuses_an_unsafe_name"
implementation:
  - gangway/api/presets.py
  - frontend/src/app/pages/presets/presets.page.ts
scope:
  - gangway/api/presets.py
  - frontend/src/app/pages/presets
---

# A preset name uses only safe characters

A preset name must match `^[a-zA-Z0-9 \-_]+$`. The save and the rename must refuse a different
name with 400. The web UI must refuse the same names before it sends them.

Reason: The name becomes a file name. A `/` or `..` must not reach the file system.

Test: `tests/test_presets_api.py:test_save_refuses_an_unsafe_name`,
`tests/test_presets_api.py:test_rename_refuses_an_unsafe_name`,
`frontend/src/app/pages/presets/presets.page.spec.ts` (`nameError`).
