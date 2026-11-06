---
id: "000064"
title: A track deletion removes the person
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_xovis.py:test_delete_track_removes_the_person"
implementation:
  - gangway/xovis/server.py
scope:
  - gangway/xovis/server.py
---

# A track deletion removes the person

A `DeleteTrack` event must remove the person from the tracked persons.

Test: `tests/test_xovis.py:test_delete_track_removes_the_person`.
