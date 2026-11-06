---
id: "000038"
title: The frontend uses the kit components and the semantic tokens
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - frontend/src/app
scope:
  - frontend/src
---

# The frontend uses the kit components and the semantic tokens

A view must use the components of `@stupa-makers/ui-kit` where the kit has one. A style must use
the semantic color tokens of the kit. It must not use a literal color. The rules of
`STUPA-Workflow/frontend/DESIGN_SYSTEM.md` apply.

Reason: The kit gives the same look in all STUPA-MAKERS apps and in both themes.

Test: Review.
