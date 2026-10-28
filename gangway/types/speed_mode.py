"""The `SpeedMode` type."""

from enum import StrEnum


class SpeedMode(StrEnum):
    """The direction of the time change of `proximity_speed`.

    The members are strings, so the plain strings of the YAML config
    compare equal to them.

    Attributes:
        SPEED_UP: Make the animation faster near the point.
        SLOW_DOWN: Make the animation slower near the point.
    """

    SPEED_UP = "speed up"
    SLOW_DOWN = "slow down"
