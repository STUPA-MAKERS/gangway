"""The `Strip` type."""

from dataclasses import dataclass

from .point import Point


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
