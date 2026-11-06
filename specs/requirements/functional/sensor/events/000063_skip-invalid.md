---
id: "000063"
title: An invalid event item is skipped
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_xovis.py:test_parse_event_skips_invalid_items"
  - "tests/test_xovis.py:test_iter_events_is_lazy_and_skips"
implementation:
  - gangway/xovis/model.py
scope:
  - gangway/xovis/model.py
---

# An invalid event item is skipped

The parser must skip an event item that it cannot read. The other items of the request must go
to the subscribers.

Reason: One bad item must not lose the persons of the whole request.

Test: `tests/test_xovis.py:test_parse_event_skips_invalid_items`,
`tests/test_xovis.py:test_iter_events_is_lazy_and_skips`.
