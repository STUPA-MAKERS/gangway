---
id: "000071"
title: Days and weeks use the local timezone
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_start_of_week_is_monday_midnight"
  - "tests/test_sensor_stats.py:test_bucket_sums_hours_by_local_day_across_the_dst_change"
implementation:
  - gangway/api/stats.py
  - gangway/xovis/sensor_api.py
scope:
  - gangway/api/stats.py
  - gangway/xovis/sensor_api.py
---

# Days and weeks use the local timezone

The days and the weeks of the statistics must use the timezone of `GANGWAY_TIMEZONE`, with the
default `Europe/Berlin`. A week must start on Monday at 00:00. An hour range must count real
hours, also on the day of a change of the summer time.

Test: `tests/test_sensor_stats.py:test_start_of_week_is_monday_midnight`,
`tests/test_sensor_stats.py:test_bucket_sums_hours_by_local_day_across_the_dst_change`.
