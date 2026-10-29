"""The `SceneContext` type."""

from dataclasses import dataclass

from .audio_state import SILENT_AUDIO, AudioState
from .led import LED
from .rectangle import Rectangle


@dataclass
class SceneContext:
    """The scene data that each animation call gets.

    Attributes:
        floor: The floor area.
        leds: All LEDs of the installation.
        audio: The sound analysis of the frame. The beat times use the
            clock of the ``time`` argument of the animations.
    """

    floor: Rectangle
    leds: list[LED]
    audio: AudioState = SILENT_AUDIO
