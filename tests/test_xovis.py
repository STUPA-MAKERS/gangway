"""Tests for the Xovis event parser and receiver."""

import http.client
import json

import numpy as np
import pytest
from numpy.typing import NDArray

from gangway.config import CONFIG
from gangway.types import TrackedPoint
from gangway.xovis.homographic_projection import apply_transform
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
    """An item with no type, an unknown type or a missing key gives None.

    §F/sensor/events/000063
    """
    assert parse_event(_raw(item)) is None


def test_iter_events_is_lazy_and_skips() -> None:
    """iter_events keeps the order and drops the items it cannot parse.

    §F/sensor/events/000063
    """
    items = [_raw(SKIPPED[0]), _raw(CASES[0][0]), _raw(SKIPPED[3]), _raw(CASES[2][0])]
    events = iter_events(items)
    assert not isinstance(events, list)
    assert list(events) == [CASES[0][1], CASES[2][1]]


def test_server_notifies_both_subscriber_kinds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Event and position subscribers both get the events of one request.

    §F/sensor/events/000062
    """

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


def _positions(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[XOVISServer, list[list[TrackedPoint]]]:
    def identity(points: list[tuple[int, int]]) -> NDArray[np.float64]:
        return np.array(points, dtype=np.float64)

    monkeypatch.setattr("gangway.xovis.server.apply_transform", identity)
    server = XOVISServer()
    received: list[list[TrackedPoint]] = []
    server.subscribe_position(received.append)
    return server, received


def _track(kind: str, timestamp: int, x: int) -> EventJson:
    return _raw(
        {"type": kind, "timestamp": timestamp, "object": {**OBJ, "x": x}},
    )


def test_delete_track_removes_the_person(monkeypatch: pytest.MonkeyPatch) -> None:
    """After a DeleteTrack, the position subscribers get no person.

    §F/sensor/events/000064
    """
    server, received = _positions(monkeypatch)

    server.notify([_track("CreateTrack", 10, 300)])
    server.notify([_track("DeleteTrack", 11, 300)])

    assert len(received[0]) == 1
    assert received[1] == []


def test_an_older_event_does_not_move_the_person(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An event with an older or equal timestamp keeps the last position.

    §F/sensor/events/000065
    """
    server, received = _positions(monkeypatch)

    server.notify([_track("CreateTrack", 20, 300)])
    server.notify([_track("CreateTrack", 10, 100)])
    server.notify([_track("CreateTrack", 20, 100)])

    assert [p.x for p in received[-1]] == [300]


def test_projection_maps_the_reference_points_to_the_floor() -> None:
    """The four camera points of the config land on their floor points.

    §F/sensor/events/000066
    """
    floor = apply_transform(np.array(CONFIG.SRC_POINTS, dtype=np.float64))

    np.testing.assert_allclose(floor, np.array(CONFIG.DST_POINTS), atol=1e-6)


def _post(port: int, body: bytes, headers: dict[str, str]) -> int:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("POST", "/", body=body, headers=headers)
        return connection.getresponse().status
    finally:
        connection.close()


def test_receiver_answers_a_post() -> None:
    """Valid JSON gets 200, also as a chunked body, and invalid JSON gets 400.

    §F/sensor/events/000062
    """
    server = XOVISServer(host="127.0.0.1", port=0)
    received: list[Event] = []
    server.subscribe(received.append, None)
    http_server = server.start_server()
    port = http_server.server_address[1]
    body = json.dumps([CASES[0][0]]).encode()
    chunked = b"%x\r\n%s\r\n0\r\n\r\n" % (len(body), body)
    try:
        assert _post(port, body, {"Content-Type": "application/json"}) == 200
        assert _post(port, chunked, {"Transfer-Encoding": "chunked"}) == 200
        assert _post(port, b"not json", {}) == 400
    finally:
        http_server.shutdown()
        http_server.server_close()

    assert received == [CASES[0][1], CASES[0][1]]
