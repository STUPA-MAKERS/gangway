"""The `Axis` type."""

from enum import StrEnum


class Axis(StrEnum):
    """An axis of the floor plane.

    The members are strings, so the plain strings of the YAML config
    compare equal to them.

    Attributes:
        X: The x axis.
        Y: The y axis.
    """

    X = "x"
    Y = "y"
