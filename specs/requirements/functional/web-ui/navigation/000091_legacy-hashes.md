---
id: "000091"
title: Old hash links go to the new routes
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app/app.routes.ts
scope:
  - frontend/src/app/app.routes.ts
---

# Old hash links go to the new routes

The root path must redirect `#viz` to `/live`, `#animations` to `/animation` and `#presets` to
`/presets`. Every other path that has no route must go to `/live`.

Reason: Bookmarks of the old Next.js app must work.

Test: `frontend/src/app/app.routes.spec.ts`.
