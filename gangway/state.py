"""The shared run-time state of the application."""

from dataclasses import dataclass, field

from .audio import AudioCapture
from .led_controller import LEDController
from .types import TrackedPoint
from .xovis.server import XOVISServer


@dataclass
class State:
    """The components and data that the API reads.

    Attributes:
        led_controller: The render thread. It is None until the start.
        xovis_server: The sensor receiver. It is None until the start.
        objects: The last detected persons.
        audio_capture: The microphone thread. It is None until the start,
            and if the config turns the audio off.
    """

    led_controller: LEDController | None = None
    xovis_server: XOVISServer | None = None
    objects: list[TrackedPoint] = field(default_factory=list[TrackedPoint])
    audio_capture: AudioCapture | None = None


STATE = State()
"""The global state instance."""
