---
id: "000074"
title: The heat map is cropped to its picture
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_sensor_stats.py:test_prepare_heatmap_crops_the_frame"
implementation:
  - gangway/api/stats.py
scope:
  - gangway/api/stats.py
---

# The heat map is cropped to its picture

`GET /api/stats/heatmap` must remove the transparent frame of the sensor image. The PNG must
have no alpha channel. The answer must have `Cache-Control: max-age=300`.

Reason: A browser shows the frame in the color of the page.

Test: `tests/test_sensor_stats.py:test_prepare_heatmap_crops_the_frame`.
