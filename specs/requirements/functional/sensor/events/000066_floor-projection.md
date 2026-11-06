---
id: "000066"
title: Positions are projected to the floor
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/xovis/homographic_projection.py
scope:
  - gangway/xovis
  - config.yaml
---

# Positions are projected to the floor

The receiver must map each camera position to the floor with the homography from
`projection.src_points` to `projection.dst_points`.

Test: Review.
