"""The `TrackedPoint` type."""

from dataclasses import dataclass

from .point import Point


@dataclass
class TrackedPoint(Point):
    """A detected person on the floor.

    Attributes:
        id: The track ID that the sensor gives to the person.
        timestamp: The time of the measurement in seconds.
    """

    id: int = 0
    timestamp: float = 0.0
