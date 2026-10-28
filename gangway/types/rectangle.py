"""The `Rectangle` type."""

from dataclasses import dataclass

from .point import Point


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
