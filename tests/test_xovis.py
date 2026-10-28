"""Tests for the Xovis event parser and receiver."""

import json

import numpy as np
import pytest
from numpy.typing import NDArray

from gangway.types import TrackedPoint
from gangway.xovis.model import (
    CreateTrack,
    DeleteTrack,
    Event,
    EventCountItem,
    EventJson,
    EventObject,
    LineCount,
    LineCrossing,
    ZoneDwellTime,
    ZoneEntry,
    ZoneExit,
    iter_events,
    parse_event,
)
from gangway.xovis.server import XOVISServer

OBJ = {"id": 1, "x": 300, "y": 200, "height": 170}
COUNT = {"id": 5, "name": "zone"}
EVENT_OBJECT = EventObject(id=1, x=300, y=200, height=170)
COUNT_ITEM = EventCountItem(id=5, name="zone")

# The test items are plain dicts, as json.loads returns them.
CASES: list[tuple[object, Event]] = [
    (
        {"type": "CreateTrack", "timestamp": 10, "object": OBJ},
        CreateTrack(timestamp=10, object=EVENT_OBJECT),
    ),
    (
        {"type": "DeleteTrack", "timestamp": 11, "object": OBJ},
        DeleteTrack(timestamp=11, object=EVENT_OBJECT),
    ),
    (
        {"type": "ZoneEntry", "timestamp": 12, "object": OBJ, "countItem": COUNT},
        ZoneEntry(timestamp=12, object=EVENT_OBJECT, count_item=COUNT_ITEM),
    ),
    (
        {"type": "ZoneExit", "timestamp": 13, "object": OBJ, "countItem": COUNT},
        ZoneExit(timestamp=13, object=EVENT_OBJECT, count_item=COUNT_ITEM),
    ),
    (
        {
            "type": "ZoneDwellTime",
            "timestamp": 14,
            "object": OBJ,
            "countItem": COUNT,
            "dwellTime": 3,
            "lastExitTime": 4,
            "createdInside": True,
            "deletedInside": False,
        },
        ZoneDwellTime(
            timestamp=14,
            object=EVENT_OBJECT,
            count_item=COUNT_ITEM,
            dwell_time=3,
            last_exit_time=4,
            created_inside=True,
            deleted_inside=False,
        ),
    ),
    (
        {
            "type": "LineCrossing",
            "timestamp": 15,
            "direction": "fw",
            "object": OBJ,
            "countItem": COUNT,
        },
        LineCrossing(
            timestamp=15, direction="fw", object=EVENT_OBJECT, count_item=COUNT_ITEM
        ),
    ),
    (
        {
            "type": "LineCount",
            "timestamp": 16,
            "direction": "bw",
            "object": OBJ,
            "countItem": COUNT,
        },
        LineCount(
            timestamp=16, direction="bw", object=EVENT_OBJECT, count_item=COUNT_ITEM
        ),
    ),
]

SKIPPED: list[object] = [
    {"timestamp": 1, "object": OBJ},
    {"type": "Unknown", "timestamp": 1, "object": OBJ},
    {"type": "CreateTrack", "object": OBJ},
    {"type": "ZoneEntry", "timestamp": 1, "object": OBJ},
    {"type": "ZoneDwellTime", "timestamp": 1, "object": OBJ, "countItem": COUNT},
    {"type": "LineCrossing", "timestamp": 1, "object": OBJ, "countItem": COUNT},
]


def _raw(item: object) -> EventJson:
    # A JSON round trip gives untyped data, the same as a sensor request.
    return json.loads(json.dumps(item))


@pytest.mark.parametrize(("item", "expected"), CASES)
def test_parse_event(item: object, expected: Event) -> None:
    """Each known event type gives its event class."""
    assert parse_event(_raw(item)) == expected


@pytest.mark.parametrize("item", SKIPPED)
def test_parse_event_skips_invalid_items(item: object) -> None:
    """An item with no type, an unknown type or a missing key gives None."""
    assert parse_event(_raw(item)) is None


def test_iter_events_is_lazy_and_skips() -> None:
    """iter_events keeps the order and drops the items it cannot parse."""
    items = [_raw(SKIPPED[0]), _raw(CASES[0][0]), _raw(SKIPPED[3]), _raw(CASES[2][0])]
    events = iter_events(items)
    assert not isinstance(events, list)
    assert list(events) == [CASES[0][1], CASES[2][1]]


def test_server_notifies_both_subscriber_kinds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Event and position subscribers both get the events of one request."""

    def identity(points: list[tuple[int, int]]) -> NDArray[np.float64]:
        return np.array(points, dtype=np.float64)

    monkeypatch.setattr("gangway.xovis.server.apply_transform", identity)
    server = XOVISServer()
    received_events: list[Event] = []
    received_positions: list[list[TrackedPoint]] = []
    server.subscribe(received_events.append, None)
    server.subscribe_position(received_positions.append)

    server.notify([_raw(CASES[0][0]), _raw(CASES[2][0])])

    assert received_events == [CASES[0][1], CASES[2][1]]
    assert received_positions == [[TrackedPoint(300, 200, id=1, timestamp=0.012)]]
