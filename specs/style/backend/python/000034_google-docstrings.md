---
id: "000034"
title: Docstrings use the Google convention
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - pyproject.toml
scope:
  - main.py
  - gangway
  - tests
---

# Docstrings use the Google convention

Every public module, class and function must have a docstring in the Google convention, with
`Args:`, `Returns:` and `Raises:` where they apply.

Reason: The docstrings are the API documentation of the animations.

Test: The `D` rules of ruff with `convention = "google"`.
