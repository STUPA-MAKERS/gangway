---
id: "000079"
title: A missing audio setting gives its default
kind: functional
status: draft
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_capture.py:test_parse_settings_reads_the_section"
  - "tests/test_config.py:test_audio_section"
implementation:
  - gangway/audio/settings.py
  - gangway/api/config.py
scope:
  - gangway/audio/settings.py
  - gangway/api/config.py
---

# A missing audio setting gives its default

A missing `audio` section or a missing key must give the default:

| Key | Default |
| --- | --- |
| `enabled` | `true` |
| `device` | `AK5371` |
| `sample_rate` | `22050` |
| `block_size` | `512` |
| `noise_floor` | `0.01` |
| `bass_gain` | `4.0` |

Reason: Config files from before the audio animations must work.

Test: `tests/test_audio_capture.py:test_parse_settings_reads_the_section`,
`tests/test_config.py:test_audio_section`.
