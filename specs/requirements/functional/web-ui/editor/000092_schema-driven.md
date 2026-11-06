---
id: "000092"
title: The editor builds its form from the animation schema
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_api.py:test_animations_endpoint_lists_the_audio_animations"
implementation:
  - frontend/src/app/features/animation-editor/schema.ts
  - gangway/api/animations.py
scope:
  - frontend/src/app/features/animation-editor
  - gangway/api/animations.py
---

# The editor builds its form from the animation schema

The animation editor must build its controls from `GET /api/animations/`. A new animation in the
backend must not need a change in `frontend/`.

Test: `frontend/src/app/features/animation-editor/schema.spec.ts`.
