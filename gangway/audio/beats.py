"""The beat tracker: the aubio online tempo tracker, block by block.

aubio finds onsets, estimates the tempo from them and puts the beats on a
grid with that tempo. A beat in the grid shows also where the onset is weak,
and an onset off the grid gives no beat. This keeps the beats in time with
the music, which a threshold on each onset cannot do.

aubio can also drop the beats of a quiet hop, but a beat of the grid often
falls in the quiet hop just before a kick. So the tracker drops a beat only
when the mean level of the last `GATE_TIME` seconds is below the noise floor.
"""

from collections import deque

import aubio
import numpy as np

from . import dsp

WINDOW = 1024
"""The number of samples in the analysis window of aubio."""

HOP = 256
"""The number of samples that aubio analyzes in one step."""

GATE_TIME = 1.0
"""The time in seconds of the level that gates the beats."""


class BeatTracker:
    """Find the beats in a stream of blocks.

    The tracker keeps the state of aubio, so make one tracker for each
    stream. A block can have any size: the tracker keeps the samples that do
    not fill a hop for the next block.
    """

    def __init__(self, sample_rate: int, noise_floor: float) -> None:
        """Make a tracker.

        Args:
            sample_rate: The sample rate in hertz.
            noise_floor: The RMS value that counts as silence. No beat
                shows while the recent level is below it.
        """
        self._rate = sample_rate
        self._floor_square = noise_floor**2
        self._tempo = aubio.tempo("default", WINDOW, HOP, sample_rate)
        self._pending = np.zeros(0, dtype=np.float32)
        self._received = 0
        self._gate_len = max(1, round(GATE_TIME * sample_rate))
        self._squares: deque[tuple[int, float]] = deque()
        self._gate_samples = 0
        self._gate_sum = 0.0

    @property
    def tempo(self) -> float:
        """The tempo estimate of aubio in beats per minute."""
        return self._tempo.get_bpm()

    def feed(self, block: dsp.Samples, now: float) -> float | None:
        """Analyze one block.

        Args:
            block: The new mono samples.
            now: The time of the end of the block in seconds.

        Returns:
            The time of the beat in the block, or None. aubio gives the beat
            time in samples, so the time is earlier than ``now``.
        """
        self._add_to_gate(block)
        self._received += block.size
        samples = np.concatenate((self._pending, block.astype(np.float32)))
        beat = False
        start = 0
        while start + HOP <= samples.size:
            beat = bool(self._tempo(samples[start : start + HOP])[0]) or beat
            start += HOP
        self._pending = samples[start:]
        if not beat or self._gate_sum < self._floor_square * self._gate_samples:
            return None
        return now - (self._received - self._tempo.get_last()) / self._rate

    def _add_to_gate(self, block: dsp.Samples) -> None:
        """Add a block to the level window and drop the blocks that left it."""
        self._squares.append((block.size, float(np.sum(block**2))))
        self._gate_samples += block.size
        self._gate_sum += self._squares[-1][1]
        while len(self._squares) > 1 and (
            self._gate_samples - self._squares[0][0] >= self._gate_len
        ):
            size, total = self._squares.popleft()
            self._gate_samples -= size
            self._gate_sum -= total
