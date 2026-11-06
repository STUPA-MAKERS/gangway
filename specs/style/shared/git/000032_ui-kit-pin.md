---
id: "000032"
title: The ui-kit flake input has the commit of the submodule
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - flake.nix
  - .gitmodules
scope:
  - flake.nix
  - .gitmodules
  - nix
---

# The ui-kit flake input has the commit of the submodule

The `ui-kit` input in `flake.nix` must name the same commit as the submodule
`frontend/vendor/ui-kit`. A commit that moves the submodule must change the input too.

Reason: A flake source does not hold a submodule. The Nix build of the frontend reads the kit
from the input.

Test: Compare `git submodule status` with the `ui-kit` URL in `flake.nix`.
