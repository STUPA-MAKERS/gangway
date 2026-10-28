"""The `LED` type."""

from dataclasses import dataclass

from .point import Point


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
