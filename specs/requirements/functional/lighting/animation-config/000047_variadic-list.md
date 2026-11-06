---
id: "000047"
title: A variadic parameter takes a list
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_helpers.py:test_parse_animation_var_positional"
implementation:
  - gangway/helpers.py
scope:
  - gangway/helpers.py
---

# A variadic parameter takes a list

The value of a variadic parameter, for example `animations` of `blend`, must be a list. A
different value must raise `TypeError`.

Test: `tests/test_helpers.py:test_parse_animation_var_positional`.
