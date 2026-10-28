"""The `BlendMode` type."""

from enum import StrEnum


class BlendMode(StrEnum):
    """The way that `gangway.animations.meta.blend` mixes the channels.

    The members are strings, so the plain strings of the YAML config
    compare equal to them.

    Attributes:
        AVERAGE: Use the mean of each channel.
        MAX: Use the highest value of each channel.
    """

    AVERAGE = "average"
    MAX = "max"
