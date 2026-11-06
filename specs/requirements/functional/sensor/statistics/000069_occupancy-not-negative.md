---
id: "000069"
title: The occupancy is never below zero
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_occupancy_adds_in_takes_out_and_never_goes_below_zero"
implementation:
  - gangway/xovis/sensor_api.py
scope:
  - gangway/xovis/sensor_api.py
---

# The occupancy is never below zero

The estimate must add `entered` and subtract `left`. It must not go below 0.

Test: `tests/test_sensor_stats.py:test_occupancy_adds_in_takes_out_and_never_goes_below_zero`.
