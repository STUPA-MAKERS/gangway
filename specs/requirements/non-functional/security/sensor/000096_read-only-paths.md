---
id: "000096"
title: The sensor client reads only fixed read-only paths
kind: non-functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/xovis/sensor_api.py
scope:
  - gangway/xovis/sensor_api.py
---

# The sensor client reads only fixed read-only paths

The sensor client must send only `GET` requests. It must use only these paths:
`/api/count-data/select/csv`, `/api/info/status`, `/api/info` and `/api/maps/heat/export`.

Reason: Some paths of the sensor reset or reboot it, also on `GET`.

Test: Review.
