---
id: "000070"
title: The count ranges are day, week and month
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_counts_for_a_month_gives_one_bucket_per_day"
implementation:
  - gangway/api/stats.py
scope:
  - gangway/api/stats.py
---

# The count ranges are day, week and month

`GET /api/stats/counts` must accept `span` = `day`, `week` or `month`:

- `day` gives the last 24 hours, one bucket for each hour.
- `week` gives the last 7 days, one bucket for each hour.
- `month` gives the last 30 days, one bucket for each local day.

Test: `tests/test_sensor_stats.py:test_counts_for_a_month_gives_one_bucket_per_day`.
