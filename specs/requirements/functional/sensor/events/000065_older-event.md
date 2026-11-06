---
id: "000065"
title: An older event does not move a person
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
tests:
  - "tests/test_xovis.py:test_an_older_event_does_not_move_the_person"
implementation:
  - gangway/xovis/server.py
scope:
  - gangway/xovis/server.py
---

# An older event does not move a person

An event with a timestamp that is not newer than the last event of the same track must not
change the position of the person.

Reason: The sensor can deliver events out of order.

Test: `tests/test_xovis.py:test_an_older_event_does_not_move_the_person`.
