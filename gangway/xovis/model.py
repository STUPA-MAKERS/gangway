"""Models for the events that the Xovis sensor sends over HTTP."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Literal, TypedDict

# The *Json TypedDicts describe the raw JSON items. The sensor uses camelCase
# keys, so these classes keep them.


class EventObjectJson(TypedDict):
    """The tracked object of an event, as the sensor sends it.

    Attributes:
        id: The track ID.
        x: The x position in the camera image.
        y: The y position in the camera image.
        height: The height of the person.
    """

    id: int
    x: int
    y: int
    height: int


class EventCountItemJson(TypedDict):
    """The count item of an event, as the sensor sends it.

    Attributes:
        id: The ID of the zone or line.
        name: The name of the zone or line.
    """

    id: int
    name: str


class TrackEventJson(TypedDict):
    """A track event, as the sensor sends it.

    Attributes:
        type: The event type.
        timestamp: The time of the event in milliseconds.
        object: The tracked object.
    """

    type: Literal["CreateTrack", "DeleteTrack"]
    timestamp: int
    object: EventObjectJson


class ZoneEventJson(TypedDict):
    """A zone entry or zone exit event, as the sensor sends it.

    Attributes:
        type: The event type.
        timestamp: The time of the event in milliseconds.
        object: The tracked object.
        countItem: The zone.
    """

    type: Literal["ZoneEntry", "ZoneExit"]
    timestamp: int
    object: EventObjectJson
    countItem: EventCountItemJson


class ZoneDwellTimeJson(TypedDict):
    """A zone dwell time event, as the sensor sends it.

    Attributes:
        type: The event type.
        timestamp: The time of the event in milliseconds.
        object: The tracked object.
        countItem: The zone.
        dwellTime: The time in the zone.
        lastExitTime: The time of the last exit.
        createdInside: True if the track started in the zone.
        deletedInside: True if the track ended in the zone.
    """

    type: Literal["ZoneDwellTime"]
    timestamp: int
    object: EventObjectJson
    countItem: EventCountItemJson
    dwellTime: int
    lastExitTime: int
    createdInside: bool
    deletedInside: bool


class LineEventJson(TypedDict):
    """A line crossing or line count event, as the sensor sends it.

    Attributes:
        type: The event type.
        timestamp: The time of the event in milliseconds.
        direction: The direction of the crossing.
        object: The tracked object.
        countItem: The line.
    """

    type: Literal["LineCrossing", "LineCount"]
    timestamp: int
    direction: str
    object: EventObjectJson
    countItem: EventCountItemJson


type EventJson = TrackEventJson | ZoneEventJson | ZoneDwellTimeJson | LineEventJson
"""One raw event item of a sensor request."""


@dataclass(kw_only=True)
class EventObject:
    """The tracked object of an event.

    Attributes:
        id: The track ID.
        x: The x position in the camera image.
        y: The y position in the camera image.
        height: The height of the person.
    """

    id: int
    x: int
    y: int
    height: int


@dataclass(kw_only=True)
class EventCountItem:
    """The zone or line of a count event.

    Attributes:
        id: The ID of the zone or line.
        name: The name of the zone or line.
    """

    id: int
    name: str


@dataclass(kw_only=True)
class Event:
    """The base class of all events.

    Attributes:
        timestamp: The time of the event in milliseconds.
        object: The tracked object.
    """

    timestamp: int
    object: EventObject


@dataclass(kw_only=True)
class CountEvent(Event):
    """The base class of the events for a zone or a line.

    Attributes:
        count_item: The zone or line.
    """

    count_item: EventCountItem


@dataclass(kw_only=True)
class CreateTrack(Event):
    """The sensor starts to track a person."""

    type: str = "CreateTrack"


@dataclass(kw_only=True)
class DeleteTrack(Event):
    """The sensor stops to track a person."""

    type: str = "DeleteTrack"


@dataclass(kw_only=True)
class ZoneExit(CountEvent):
    """A person leaves a zone."""

    type: str = "ZoneExit"


@dataclass(kw_only=True)
class ZoneEntry(CountEvent):
    """A person enters a zone."""

    type: str = "ZoneEntry"


@dataclass(kw_only=True)
class ZoneDwellTime(CountEvent):
    """A person was in a zone for a time.

    Attributes:
        dwell_time: The time in the zone.
        last_exit_time: The time of the last exit.
        created_inside: True if the track started in the zone.
        deleted_inside: True if the track ended in the zone.
    """

    dwell_time: int
    last_exit_time: int
    created_inside: bool
    deleted_inside: bool
    type: str = "ZoneDwellTime"


@dataclass(kw_only=True)
class LineCrossing(CountEvent):
    """A person crosses a line.

    Attributes:
        direction: The direction of the crossing.
    """

    direction: str
    type: str = "LineCrossing"


@dataclass(kw_only=True)
class LineCount(CountEvent):
    """The sensor counts a person at a line.

    Attributes:
        direction: The direction of the crossing.
    """

    direction: str
    type: str = "LineCount"


def parse_event(item: EventJson) -> Event | None:
    """Convert one raw event item to an event.

    Args:
        item: The raw event item.

    Returns:
        The event. None if the type is missing or unknown, or if a key of a
        known type is missing. The function does not raise KeyError for an
        incomplete item.
    """
    match item:
        case {
            "type": "CreateTrack" | "DeleteTrack" as kind,
            "timestamp": timestamp,
            "object": obj,
        }:
            track_cls = CreateTrack if kind == "CreateTrack" else DeleteTrack
            return track_cls(timestamp=timestamp, object=EventObject(**obj))
        case {
            "type": "ZoneEntry" | "ZoneExit" as kind,
            "timestamp": timestamp,
            "object": obj,
            "countItem": count_item,
        }:
            zone_cls = ZoneEntry if kind == "ZoneEntry" else ZoneExit
            return zone_cls(
                timestamp=timestamp,
                object=EventObject(**obj),
                count_item=EventCountItem(**count_item),
            )
        case {
            "type": "ZoneDwellTime",
            "timestamp": timestamp,
            "object": obj,
            "countItem": count_item,
            "dwellTime": dwell_time,
            "lastExitTime": last_exit_time,
            "createdInside": created_inside,
            "deletedInside": deleted_inside,
        }:
            return ZoneDwellTime(
                timestamp=timestamp,
                object=EventObject(**obj),
                count_item=EventCountItem(**count_item),
                dwell_time=dwell_time,
                last_exit_time=last_exit_time,
                created_inside=created_inside,
                deleted_inside=deleted_inside,
            )
        case {
            "type": "LineCrossing" | "LineCount" as kind,
            "timestamp": timestamp,
            "direction": direction,
            "object": obj,
            "countItem": count_item,
        }:
            line_cls = LineCrossing if kind == "LineCrossing" else LineCount
            return line_cls(
                timestamp=timestamp,
                direction=direction,
                object=EventObject(**obj),
                count_item=EventCountItem(**count_item),
            )
        case _:
            return None


def iter_events(items: Iterable[EventJson]) -> Iterator[Event]:
    """Convert raw event items to events, one at a time.

    The function skips the items that `parse_event` cannot convert.

    Args:
        items: The raw event items.

    Returns:
        A lazy iterator over the events, in the order of the items. It can be
        consumed only once.
    """
    return (event for item in items if (event := parse_event(item)) is not None)
