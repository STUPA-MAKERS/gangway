---
id: "000046"
title: An unknown function or parameter is refused
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_helpers.py:test_parse_animation_unknown_function"
  - "tests/test_helpers.py:test_parse_animation_unknown_param"
  - "tests/test_api.py:test_update_config_rejects_a_bad_audio_parameter"
implementation:
  - gangway/helpers.py
  - gangway/api/models.py
scope:
  - gangway/helpers.py
  - gangway/api
---

# An unknown function or parameter is refused

An animation config with an unknown function name or an unknown parameter must raise
`ValueError` when it loads. The config API must refuse it with 422.

Reason: A typing error must not give an animation that silently ignores a value.

Test: `tests/test_helpers.py:test_parse_animation_unknown_function`,
`tests/test_helpers.py:test_parse_animation_unknown_param`,
`tests/test_api.py:test_update_config_rejects_a_bad_audio_parameter`.
