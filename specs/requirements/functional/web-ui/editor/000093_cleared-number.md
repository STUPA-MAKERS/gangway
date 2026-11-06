---
id: "000093"
title: A cleared number uses the backend default
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app/features/animation-editor/animation-editor.component.ts
scope:
  - frontend/src/app/features/animation-editor
---

# A cleared number uses the backend default

When the user clears a number field, the editor must remove the parameter from the draft. It
must not send 0 or an empty value.

Reason: The default of the animation function then applies.

Test: `frontend/src/app/features/animation-editor/animation-editor.component.spec.ts`.
