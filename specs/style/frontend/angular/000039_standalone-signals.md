---
id: "000039"
title: Components are standalone with signals and OnPush
kind: style
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app
scope:
  - frontend/src
---

# Components are standalone with signals and OnPush

A component must be standalone. It must keep its state in signals. It must use
`ChangeDetectionStrategy.OnPush`.

Test: Review.
