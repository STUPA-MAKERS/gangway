---
id: "000072"
title: Sensor answers are cached
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_client_caches_a_request"
implementation:
  - gangway/xovis/sensor_api.py
scope:
  - gangway/xovis/sensor_api.py
---

# Sensor answers are cached

The sensor client must keep each answer for a fixed time: the counts 60 s, the status 30 s, the
device info 3600 s and the heat map 300 s.

Reason: Each page load asks for many values. The sensor must not get a request for each.

Test: `tests/test_sensor_stats.py:test_client_caches_a_request`.
