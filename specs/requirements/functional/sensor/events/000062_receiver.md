---
id: "000062"
title: The sensor events arrive on port 8081
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_xovis.py:test_server_notifies_both_subscriber_kinds"
implementation:
  - gangway/xovis/server.py
scope:
  - gangway/xovis/server.py
---

# The sensor events arrive on port 8081

The Xovis receiver must accept `POST` requests with a JSON list of events on port 8081. It must
answer 200 for valid JSON and 400 for invalid JSON. It must accept a chunked body.

Test: `tests/test_xovis.py:test_server_notifies_both_subscriber_kinds`.
