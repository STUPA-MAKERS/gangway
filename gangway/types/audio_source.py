"""The `AudioSource` type."""

from enum import StrEnum


class AudioSource(StrEnum):
    """A value of `AudioState` that an animation can follow.

    The members are strings, so the plain strings of the YAML config
    compare equal to them.

    Attributes:
        LEVEL: The loudness of the full signal.
        BASS: The energy of the bass band.
        MID: The energy of the mid band.
        TREBLE: The energy of the treble band.
    """

    LEVEL = "level"
    BASS = "bass"
    MID = "mid"
    TREBLE = "treble"
