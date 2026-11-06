---
id: "000049"
title: A schedule window can go past midnight
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_meta_animations.py:test_schedule_window_past_midnight"
implementation:
  - gangway/animations/meta/schedule.py
scope:
  - gangway/animations/meta/schedule.py
---

# A schedule window can go past midnight

`schedule` must show `primary` from `start` to `end` and `secondary` at all other times. If
`start` is after `end`, the window must go past midnight.

Test: `tests/test_meta_animations.py:test_schedule_window_past_midnight`.
