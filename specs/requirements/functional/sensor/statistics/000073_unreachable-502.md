---
id: "000073"
title: An unreachable sensor gives 502
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_client_reports_an_unreachable_sensor"
implementation:
  - gangway/api/stats.py
  - gangway/xovis/sensor_api.py
scope:
  - gangway/api/stats.py
---

# An unreachable sensor gives 502

If the sensor does not answer or answers with an error, the statistics endpoints must give 502.

Test: `tests/test_sensor_stats.py:test_client_reports_an_unreachable_sensor`.
