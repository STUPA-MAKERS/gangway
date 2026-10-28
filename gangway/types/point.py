"""The `Point` type."""

import builtins
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self


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
