---
id: "000088"
title: The web UI sends no key first
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app/core/api/api-key.interceptor.ts
scope:
  - frontend/src/app/core/api
---

# The web UI sends no key first

A request to `/api/` must go out without `X-API-Key` while the browser has no stored key. With a
stored key, the request must have it in `X-API-Key`.

Reason: On the SSO tunnel nginx adds the key, so the browser never needs one there.

Test: `frontend/src/app/core/api/api-key.interceptor.spec.ts`.
