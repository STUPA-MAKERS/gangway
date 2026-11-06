---
id: "000048"
title: Times of day stay strings in YAML
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_yaml_loader.py:test_times_of_day_stay_strings"
  - "tests/test_yaml_loader.py:test_other_values_load_as_with_safe_load"
  - "tests/test_yaml_loader.py:test_dumped_times_load_back_unchanged"
implementation:
  - gangway/yaml_loader.py
scope:
  - gangway/yaml_loader.py
---

# Times of day stay strings in YAML

The config loader must read a value such as `13:30` as the string `"13:30"`. It must not read it
as a base 60 number. All other values must load as with `yaml.safe_load`.

Reason: PyYAML follows YAML 1.1 and reads `13:30` as 810. `schedule` needs the time.

Test: `tests/test_yaml_loader.py:test_times_of_day_stay_strings`,
`tests/test_yaml_loader.py:test_other_values_load_as_with_safe_load`,
`tests/test_yaml_loader.py:test_dumped_times_load_back_unchanged`.
