---
id: "000068"
title: The occupancy starts at zero at 04:00
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_occupancy_starts_at_zero_at_four_in_the_morning"
implementation:
  - gangway/xovis/sensor_api.py
scope:
  - gangway/xovis/sensor_api.py
---

# The occupancy starts at zero at 04:00

The estimate of the persons in the room must start at 0 at 04:00 local time each day.

Reason: A missed crossing must not stay in the estimate for more than one day.

Test: `tests/test_sensor_stats.py:test_occupancy_starts_at_zero_at_four_in_the_morning`.
