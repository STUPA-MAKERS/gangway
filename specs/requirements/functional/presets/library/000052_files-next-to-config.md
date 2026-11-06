---
id: "000052"
title: Presets are YAML files next to the config
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_presets.py:test_preset_reads_presets_next_to_config"
  - "tests/test_presets_api.py:test_list_gives_the_preset_names"
implementation:
  - gangway/api/presets.py
scope:
  - gangway/api/presets.py
  - presets
---

# Presets are YAML files next to the config

A preset must be the file `<name>.yaml` in the folder `presets/` next to the config file. The
file must hold one animation config. `GET /api/presets/` must give the names of all preset
files.

Reason: On the Pi the source tree is read-only. The config and the presets live in the state
folder.

Test: `tests/test_presets.py:test_preset_reads_presets_next_to_config`,
`tests/test_presets_api.py:test_list_gives_the_preset_names`.
