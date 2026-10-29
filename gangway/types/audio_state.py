"""The `AudioState` type and the `SILENT_AUDIO` snapshot."""

import math
from dataclasses import dataclass, replace

from .audio_source import AudioSource


@dataclass(frozen=True)
class AudioState:
    """A snapshot of the sound analysis that the animations read.

    The audio thread makes a new snapshot for each block of samples. The
    snapshot never changes, so a frame can read it from any thread.

    Attributes:
        level: The loudness, from 0 (silence) to 1 (the recent peak).
        bass: The energy of the bass band (about 40 to 150 Hz), from 0 to 1.
        mid: The energy of the mid band (about 150 to 2000 Hz), from 0 to 1.
        treble: The energy of the treble band (about 2000 to 8000 Hz), from
            0 to 1.
        spectrum: The energy of narrower bands from low to high frequency,
            each from 0 to 1. The tuple is empty if no analysis ran.
        last_beat: The time of the last beat in seconds. Minus infinity
            means that no beat occurred.
        beats: The times of the recent beats in seconds, oldest first.
        beat_count: The number of beats since the start of the analysis.
        tempo: The tempo from the recent beats in beats per minute, or 0 if
            there are too few beats.
    """

    level: float = 0.0
    bass: float = 0.0
    mid: float = 0.0
    treble: float = 0.0
    spectrum: tuple[float, ...] = ()
    last_beat: float = -math.inf
    beats: tuple[float, ...] = ()
    beat_count: int = 0
    tempo: float = 0.0

    def value(self, source: AudioSource) -> float:
        """Get the value of one source.

        Args:
            source: The source. A value that is not a member gives the
                level.

        Returns:
            The value, from 0 to 1.
        """
        match source:
            case AudioSource.BASS:
                return self.bass
            case AudioSource.MID:
                return self.mid
            case AudioSource.TREBLE:
                return self.treble
            case _:
                return self.level

    def shifted(self, offset: float) -> "AudioState":
        """Move the beat times to a different clock.

        Args:
            offset: The time to add to each beat time in seconds.

        Returns:
            A copy with the moved beat times.
        """
        return replace(
            self,
            last_beat=self.last_beat + offset,
            beats=tuple(t + offset for t in self.beats),
        )


SILENT_AUDIO = AudioState()
"""The snapshot with no sound and no beats."""
