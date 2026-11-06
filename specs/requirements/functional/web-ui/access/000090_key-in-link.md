---
id: "000090"
title: A key in the link is stored and removed from the address
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app/core/api/api-key.service.ts
scope:
  - frontend/src/app/core/api
---

# A key in the link is stored and removed from the address

The web UI must store the value of the query parameter `apiKey` in `localStorage`. It must then
remove the parameter from the address bar.

Reason: The key must not stay in the browser history.

Test: Review.
