---
id: "000027"
title: Commands run in the Nix dev shell
kind: style
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - modules/parts/packages.nix
scope:
  - flake.nix
  - modules/parts/packages.nix
---

# Commands run in the Nix dev shell

The Python checks, the Python tests and the frontend commands must run in `nix develop`. A
command must not use a Python or a Node from outside the shell.

Reason: The shell pins Python 3.13, aubio and the other packages of the Pi. A different version
gives different results.
