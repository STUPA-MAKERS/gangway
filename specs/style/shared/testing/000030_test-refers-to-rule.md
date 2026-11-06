---
id: "000030"
title: A test refers back to its rule
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - scripts/check_specs.py
scope:
  - tests
  - frontend/src
---

# A test refers back to its rule

A test that checks a rule must name the rule in its docstring with `§` and the full rule ID. The
rule must list the test in `tests`.

Reason: The reference shows which rule breaks when the test fails.

Test: `scripts/check_specs.py` finds a `§` reference that names no spec.
