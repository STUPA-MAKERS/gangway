---
id: "000033"
title: Python code passes ruff and strict basedpyright
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
  - pyproject.toml
---

# Python code passes ruff and strict basedpyright

`main.py`, `gangway/` and `tests/` must pass `ruff check` and `basedpyright` with
`typeCheckingMode = "strict"`. A new ignore must have a comment with its reason.

Reason: Strict types find a wrong animation argument before it reaches the Pi.

Test: `ruff check` and `basedpyright` in `nix develop`.
