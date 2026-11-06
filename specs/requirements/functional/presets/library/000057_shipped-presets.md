---
id: "000057"
title: Every shipped preset loads and renders
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets.py:test_shipped_preset_renders"
implementation:
  - presets
scope:
  - presets
---

# Every shipped preset loads and renders

Every file in `presets/` of the repository must load as an animation config and render a frame
without an error.

Test: `tests/test_presets.py:test_shipped_preset_renders`.
