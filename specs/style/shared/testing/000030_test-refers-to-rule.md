---
id: "000030"
title: A test refers back to its rule
kind: style
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_specs.py:test_specs_follow_the_rules_for_specs"
implementation:
  - scripts/check_specs.py
scope:
  - tests
  - frontend/src
---

# A test refers back to its rule

A Python test that checks a rule must name the rule in its docstring with `§` and the full rule
ID. The rule must list the test in `tests`. A frontend test must name the rule in a comment
above its `it` block.

Reason: The reference shows which rule breaks when the test fails.

Test: `scripts/check_specs.py` finds a Python test in `tests` without the reference, and a `§`
reference that names no spec.
