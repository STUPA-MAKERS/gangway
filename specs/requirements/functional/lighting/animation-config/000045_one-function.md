---
id: "000045"
title: An animation config names one function
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_helpers.py:test_parse_animation_simple_color"
  - "tests/test_helpers.py:test_parse_animation_function"
implementation:
  - gangway/helpers.py
scope:
  - gangway/helpers.py
  - config.yaml
  - presets
---

# An animation config names one function

A mapping with the keys `r`, `g` and `b` must give a color. A different mapping must have one
key: the registry name of an animation. A mapping value must give the keyword arguments. A
different value must give the first positional argument.

Test: `tests/test_helpers.py:test_parse_animation_simple_color`,
`tests/test_helpers.py:test_parse_animation_function`.
