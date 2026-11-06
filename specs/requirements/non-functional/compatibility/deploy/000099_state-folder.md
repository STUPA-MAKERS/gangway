---
id: "000099"
title: The app state lives in /var/lib/gangway
kind: non-functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - modules/nixos/gangway.nix
scope:
  - modules/nixos/gangway.nix
---

# The app state lives in /var/lib/gangway

On the Pi, `config.yaml` and `presets/` must be in `/var/lib/gangway`. `GANGWAY_CONFIG` must
point to the config file there.

Reason: The Nix store is read-only. The web UI changes the config and the presets.

Test: Review.
