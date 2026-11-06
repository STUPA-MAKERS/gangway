"""Tests for the beat tracker with synthetic kick drums."""

from itertools import pairwise

import numpy as np

from gangway.audio.beats import BeatTracker
from gangway.audio.dsp import Samples

RATE = 22050
BLOCK = 512
FLOOR = 0.01
PERIOD = 0.5
"""The kick period of the tests: 120 beats per minute."""

GRID = tuple(0.1 + PERIOD * i for i in range(40))


def _kicks(times: tuple[float, ...], seconds: float, noise: float = 0.005) -> Samples:
    """Get kick drums at ``times`` over a little noise."""
    rng = np.random.default_rng(0)
    signal = rng.normal(0, noise, round(seconds * RATE))
    t = np.arange(round(0.12 * RATE)) / RATE
    pitch = 50 + 80 * np.exp(-t * 30)
    kick = 0.5 * np.sin(2 * np.pi * pitch * t) * np.exp(-t * 25)
    for time in times:
        start = round(time * RATE)
        part = signal[start : start + kick.size]
        part += kick[: part.size]
    return signal


def _beats(signal: Samples) -> list[float]:
    """Feed a signal block by block and get the beat times."""
    tracker = BeatTracker(RATE, FLOOR)
    found: list[float] = []
    for start in range(0, signal.size - BLOCK + 1, BLOCK):
        beat = tracker.feed(signal[start : start + BLOCK], (start + BLOCK) / RATE)
        if beat is not None:
            found.append(beat)
    return found


def _near(beats: list[float], time: float) -> bool:
    return any(abs(beat - time) <= 0.03 for beat in beats)


def test_steady_kicks_give_a_steady_grid() -> None:
    """After a few seconds, each kick gives one beat at the kick time.

    §S/shared/testing/000031
    """
    beats = [b for b in _beats(_kicks(GRID, 20.0)) if b > 8]
    assert all(_near(beats, kick) for kick in GRID if 8 < kick < 19.5)
    assert all(abs(b - a - PERIOD) <= 0.03 for a, b in pairwise(beats))


def test_a_missing_kick_still_gives_a_beat() -> None:
    """The grid goes on where a kick is missing.

    §F/audio/analysis/000084
    """
    missing = (15.1, 17.1)
    kicks = tuple(k for k in GRID if all(abs(k - m) > 0.01 for m in missing))
    beats = _beats(_kicks(kicks, 20.0))
    assert all(_near(beats, m) for m in missing)


def test_a_kick_off_the_grid_gives_no_beat() -> None:
    """A single kick between two beats of the grid gives no beat.

    §F/audio/analysis/000084
    """
    extra = (14.35, 16.85)
    beats = _beats(_kicks(tuple(sorted((*GRID, *extra))), 20.0))
    assert not any(_near(beats, e) for e in extra)


def test_silence_gives_no_beats() -> None:
    """Noise below the noise floor gives no beat."""
    rng = np.random.default_rng(1)
    assert _beats(rng.normal(0, 0.002, 5 * RATE)) == []


def test_beats_stop_soon_after_the_music() -> None:
    """The beats stop about one gate time after the last kick."""
    rng = np.random.default_rng(1)
    signal = np.concatenate((_kicks(GRID, 20.0), rng.normal(0, 0.002, 5 * RATE)))
    assert max(_beats(signal)) < 21.5


def test_blocks_of_any_size_give_the_same_beats() -> None:
    """The tracker keeps the samples that do not fill a hop."""
    signal = _kicks(GRID, 12.0)
    tracker = BeatTracker(RATE, FLOOR)
    odd: list[float] = []
    size = 300
    for start in range(0, signal.size - size + 1, size):
        beat = tracker.feed(signal[start : start + size], (start + size) / RATE)
        if beat is not None:
            odd.append(beat)
    assert all(_near(odd, b) for b in _beats(signal) if b < 11.5)
