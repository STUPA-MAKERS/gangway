---
id: "000036"
title: An animation is a function of time, context, LED and persons
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - gangway/types/animation.py
scope:
  - gangway/animations
  - gangway/types/animation.py
---

# An animation is a function of time, context, LED and persons

An animation must be a callable with the parameters `(time, context, led, objects)` that returns
an `RGBCCT`. An animation factory must return such a callable or an `RGBCCT`.

Reason: The render loop calls every animation in the same way.

Test: `basedpyright` checks the `Animation` type.
