---
id: "000095"
title: The API refuses requests without a server key
kind: non-functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/api/security.py
scope:
  - gangway/api/security.py
---

# The API refuses requests without a server key

If `API_KEY` is not set or empty, every route below `/api/` must give 500.

Reason: An empty server key must not open the API.

Test: Review.
