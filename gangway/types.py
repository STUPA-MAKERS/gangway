"""Core data types for the floor geometry, the LEDs and the animations."""

import builtins
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Self

from rpi_ws2805 import RGBCCT

type YamlValue = (
    str | int | float | bool | None | list[YamlValue] | dict[str, YamlValue]
)
"""A value that ``yaml.safe_load`` can return for a plain YAML document."""


@dataclass
class Point:
    """A point or a vector on the floor plane.

    Attributes:
        x: The x coordinate.
        y: The y coordinate.
    """

    x: float = 0.0
    y: float = 0.0

    def __sub__(self, other: "Point") -> Self:
        """Return the vector from this point to ``other``.

        The result is ``other - self``, not ``self - other``. The LED
        distance math and the strip interpolation depend on this order.

        Args:
            other: The end point of the vector.

        Returns:
            A copy of this point with the coordinates of the vector.
        """
        return replace(self, x=other.x - self.x, y=other.y - self.y)

    def __add__(self, other: "Point") -> Self:
        """Add the coordinates of ``other`` to this point.

        Args:
            other: The vector to add.

        Returns:
            A copy of this point with the sum of the coordinates.
        """
        return replace(self, x=self.x + other.x, y=self.y + other.y)

    def __mul__(self, other: float) -> Self:
        """Scale the point by a factor.

        Args:
            other: The scale factor.

        Returns:
            A copy of this point with the scaled coordinates.
        """
        return replace(self, x=self.x * other, y=self.y * other)

    def __truediv__(self, other: float) -> Self:
        """Divide the coordinates by a divisor.

        Args:
            other: The divisor.

        Returns:
            A copy of this point with the divided coordinates.
        """
        return replace(self, x=self.x / other, y=self.y / other)

    @property
    def tuple(self) -> builtins.tuple[float, float]:
        """The coordinates as an ``(x, y)`` tuple."""
        return (self.x, self.y)

    @property
    def length(self) -> float:
        """The distance from the origin."""
        return (self.x**2 + self.y**2) ** 0.5

    @classmethod
    def from_tuple(cls, t: Sequence[float]) -> Self:
        """Make a point from a sequence of coordinates.

        Args:
            t: The ``x`` and ``y`` coordinates.

        Returns:
            The new point.
        """
        return cls(*t)


@dataclass
class TrackedPoint(Point):
    """A detected person on the floor.

    Attributes:
        id: The track ID that the sensor gives to the person.
        timestamp: The time of the measurement in seconds.
    """

    id: int = 0
    timestamp: float = 0.0


@dataclass
class Rectangle:
    """An axis-aligned rectangle from two corners.

    Attributes:
        p1: The first corner.
        p2: The opposite corner.
    """

    p1: Point
    p2: Point

    @property
    def width(self) -> float:
        """The size along the x axis."""
        return abs(self.p2.x - self.p1.x)

    @property
    def height(self) -> float:
        """The size along the y axis."""
        return abs(self.p2.y - self.p1.y)

    @property
    def center(self) -> Point:
        """The center point."""
        return Point(
            x=(self.p1.x + self.p2.x) / 2,
            y=(self.p1.y + self.p2.y) / 2,
        )


@dataclass
class Strip:
    """One physical LED strip segment.

    Attributes:
        index: The index of the first LED of the segment in the LED chain.
        len: The number of LEDs in the segment.
        start: The floor position of the start of the segment.
        end: The floor position of the end of the segment.
    """

    index: int
    len: int
    start: Point
    end: Point


@dataclass
class LED:
    """One LED with its position on the floor.

    Attributes:
        index: The index of the LED in the LED chain.
        p: The floor position.
        strip_index: The position of the strip segment in the config.
    """

    index: int
    p: Point
    strip_index: int = 0


@dataclass
class SceneContext:
    """The scene data that each animation call gets.

    Attributes:
        floor: The floor area.
        leds: All LEDs of the installation.
    """

    floor: Rectangle
    leds: list[LED]


type Animation = Callable[[float, SceneContext, LED, Sequence[TrackedPoint]], RGBCCT]
"""Calculate the color of one LED for one frame.

The arguments are the time since the start in seconds, the scene context, the
LED, and the detected persons.
"""

type AnimationOrColor = Animation | RGBCCT
"""An animation, or a static color that is the same for all frames."""
