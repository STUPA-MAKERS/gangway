---
id: "000067"
title: The counts come from count line 0
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_parse_counts_reads_the_csv_of_the_sensor"
implementation:
  - gangway/xovis/sensor_api.py
scope:
  - gangway/xovis/sensor_api.py
---

# The counts come from count line 0

The statistics must read count line 0 of the sensor. A backward crossing must count as
`entered`. A forward crossing must count as `left`.

Reason: Line 0 points from the inside to the outside. The other line only makes the push events.

Test: `tests/test_sensor_stats.py:test_parse_counts_reads_the_csv_of_the_sensor`.
