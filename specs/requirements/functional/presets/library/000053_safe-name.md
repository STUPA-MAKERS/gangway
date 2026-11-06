---
id: "000053"
title: A preset name uses only safe characters
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
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

Test: `frontend/src/app/pages/presets/presets.page.spec.ts` (`nameError`).
