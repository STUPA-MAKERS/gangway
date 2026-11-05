"""Sound analysis of the USB microphone for the audio animations.

`AudioCapture` reads the microphone in a thread. `AudioProcess` runs that
thread in a child process, so that the LED loop cannot slow it down. The
pure functions in
`dsp` turn each block of samples into a `gangway.types.AudioState`
snapshot. The LED controller puts the latest snapshot into the scene
context of each frame.
"""

from .capture import AudioCapture, BlockSource, StreamOpener, find_device
from .process import AudioProcess
from .settings import AudioConfig, AudioSettings, parse_settings

__all__ = [
    "AudioCapture",
    "AudioConfig",
    "AudioProcess",
    "AudioSettings",
    "BlockSource",
    "StreamOpener",
    "find_device",
    "parse_settings",
]
