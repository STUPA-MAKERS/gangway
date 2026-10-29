"""Animations that react to the sound of the microphone.

The animations read `gangway.types.SceneContext.audio`. Without a
microphone the snapshot is silent, so the animations show their background.
"""

from .audio_gain import audio_gain
from .beat_pulse import beat_pulse
from .beat_ripples import beat_ripples
from .beat_switch import beat_switch
from .beat_wave import beat_wave
from .level import level
from .spectrum import spectrum

__all__ = [
    "audio_gain",
    "beat_pulse",
    "beat_ripples",
    "beat_switch",
    "beat_wave",
    "level",
    "spectrum",
]
