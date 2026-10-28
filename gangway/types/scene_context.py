"""The `SceneContext` type."""

from dataclasses import dataclass

from .led import LED
from .rectangle import Rectangle


@dataclass
class SceneContext:
    """The scene data that each animation call gets.

    Attributes:
        floor: The floor area.
        leds: All LEDs of the installation.
    """

    floor: Rectangle
    leds: list[LED]
