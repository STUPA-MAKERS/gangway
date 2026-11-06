---
id: "000050"
title: An invalid schedule window uses 18:00 to 06:00
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_meta_animations.py:test_schedule_with_an_invalid_range_uses_the_default"
implementation:
  - gangway/animations/meta/schedule.py
scope:
  - gangway/animations/meta/schedule.py
---

# An invalid schedule window uses 18:00 to 06:00

If `start` or `end` of `schedule` is not a valid `HH:MM` string, the window must be 18:00 to
06:00.

Reason: An installation must not stay dark because of one bad value.

Test: `tests/test_meta_animations.py:test_schedule_with_an_invalid_range_uses_the_default`.
