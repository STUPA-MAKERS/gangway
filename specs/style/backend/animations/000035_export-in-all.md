---
id: "000035"
title: An animation is exported by its package
kind: style
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_audio_animations.py:test_audio_animations_are_in_the_registry"
implementation:
  - gangway/config.py
  - gangway/animations
scope:
  - gangway/animations
---

# An animation is exported by its package

An animation must be in one of the packages `idle`, `responsive`, `meta` or `audio` of
`gangway/animations/`. Each module must hold one animation or a small group of similar
animations. The package must export the animation in `__all__`.

Reason: The registry in `gangway/config.py` reads only `__all__` of each package. The config and
the editor know only the animations of the registry.

Test: `tests/test_audio_animations.py:test_audio_animations_are_in_the_registry`.
