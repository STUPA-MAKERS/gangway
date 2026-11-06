---
id: "000089"
title: A refused key opens the key prompt
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app/core/api/api-key.interceptor.ts
  - frontend/src/app/app.ts
  - frontend/src/app/layout/key-prompt.component.ts
scope:
  - frontend/src/app
---

# A refused key opens the key prompt

A 401 or 403 answer to a request to `/api/` must make the shell ask for the API key.

Test: `frontend/src/app/app.spec.ts` and
`frontend/src/app/core/api/api-key.interceptor.spec.ts`.
