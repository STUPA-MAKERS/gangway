---
id: "000061"
title: GANGWAY_CONFIG names the config file
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_repository.py:test_gangway_config_names_the_config_file"
implementation:
  - gangway/config.py
scope:
  - gangway/config.py
  - main.py
---

# GANGWAY_CONFIG names the config file

The application must read the config file that `GANGWAY_CONFIG` names. Without the variable, it
must read `config.yaml` in the repository root.

Reason: The presets folder is next to the config file, and modules find it at import time.

Test: `tests/test_repository.py:test_gangway_config_names_the_config_file`.
