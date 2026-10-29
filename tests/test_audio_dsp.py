"""Tests for the sound analysis with synthetic signals."""

import math
from collections.abc import Iterable
from itertools import pairwise

import numpy as np
import pytest

from gangway.audio import dsp
from gangway.types import AudioState

RATE = 22050
BLOCK = 512
HOP = BLOCK / RATE


def _tone(freq: float, seconds: float, amplitude: float = 0.5) -> dsp.Samples:
    t = np.arange(round(seconds * RATE)) / RATE
    return amplitude * np.sin(2 * np.pi * freq * t)


def _bursts(freq: float, period: float, length: float, seconds: float) -> dsp.Samples:
    """Get a tone that is on for ``length`` seconds at the start of each period."""
    t = np.arange(round(seconds * RATE)) / RATE
    on = (t % period) < length
    return np.where(on, 0.5 * np.sin(2 * np.pi * freq * t), 0.0)


def _run(signal: dsp.Samples) -> list[AudioState]:
    """Feed a signal block by block and get the snapshot of each block."""
    params = dsp.make_params(RATE, BLOCK)
    state = dsp.start(params)
    blocks: Iterable[dsp.Samples] = (
        signal[i : i + BLOCK] for i in range(0, signal.size - BLOCK + 1, BLOCK)
    )
    snapshots: list[AudioState] = []
    for index, block in enumerate(blocks):
        state = dsp.step(params, state, block, (index + 1) * HOP)
        snapshots.append(state.snapshot)
    return snapshots


def test_silence_gives_no_level_and_no_beats() -> None:
    """Silence keeps all values at 0 and detects no beats."""
    last = _run(np.zeros(2 * RATE))[-1]
    assert (last.level, last.bass, last.mid, last.treble) == (0, 0, 0, 0)
    assert last.beat_count == 0
    assert last.beats == ()


def test_quiet_noise_below_the_floor_stays_silent() -> None:
    """Noise below the noise floor gives a level of 0."""
    rng = np.random.default_rng(1)
    last = _run(rng.normal(0, 0.002, 2 * RATE))[-1]
    assert last.level == 0
    assert last.beat_count == 0


def test_bass_bursts_give_beats_at_the_burst_period() -> None:
    """A 60 Hz burst every 0.5 s gives one beat per burst."""
    last = _run(_bursts(60, period=0.5, length=0.1, seconds=4.0))[-1]
    intervals = [b - a for a, b in pairwise(last.beats)]
    assert last.beat_count == 8
    assert all(abs(i - 0.5) <= 2 * HOP for i in intervals)
    assert math.isclose(last.tempo, 120, rel_tol=0.05)


def test_fast_bursts_respect_the_refractory_period() -> None:
    """Bursts faster than the refractory period do not trigger each time."""
    last = _run(_bursts(60, period=0.1, length=0.04, seconds=3.0))[-1]
    intervals = [b - a for a, b in pairwise(last.beats)]
    assert intervals
    assert min(intervals) >= dsp.REFRACTORY


def test_steady_tone_gives_one_beat_only() -> None:
    """A steady bass tone gives a beat at its start and then no more."""
    snapshots = _run(_tone(60, 4.0))
    assert snapshots[-1].beat_count == 1
    assert snapshots[-1].beats[0] < 0.1


def test_bass_tone_raises_bass_not_treble() -> None:
    """An 80 Hz tone gives bass energy and no treble energy."""
    last = _run(_tone(80, 1.0))[-1]
    assert last.bass > 0.9
    assert last.treble < 0.05
    assert last.spectrum[0] > 0.5
    assert last.spectrum[-1] < 0.05


def test_treble_tone_raises_treble_not_bass() -> None:
    """A 4 kHz tone gives treble energy and no bass energy."""
    last = _run(_tone(4000, 1.0))[-1]
    assert last.treble > 0.9
    assert last.bass < 0.05
    assert last.mid < 0.05


@pytest.mark.parametrize("amplitude", [0.1, 0.8])
def test_agc_brings_quiet_and_loud_rooms_to_full_scale(amplitude: float) -> None:
    """The level of a steady tone reaches about 1 for any loudness."""
    last = _run(_tone(440, 1.0, amplitude))[-1]
    assert last.level > 0.9


def test_agc_peak_decays_after_a_loud_part() -> None:
    """After a loud part, a quieter tone rises back to full scale over time."""
    signal = np.concatenate((_tone(440, 1.0, 0.8), _tone(440, 30.0, 0.1)))
    snapshots = _run(signal)
    right_after = snapshots[round(1.2 / HOP)]
    much_later = snapshots[-1]
    assert right_after.level < 0.2
    assert much_later.level > 0.9


def test_band_values_give_the_rms_of_a_tone() -> None:
    """The band value of a tone is its RMS value."""
    params = dsp.make_params(RATE, BLOCK)
    frame = _tone(1000, params.fft_size / RATE, amplitude=0.5)
    _bass, mid, _treble = dsp.band_values(params, frame, params.bands)
    assert math.isclose(mid, 0.5 / math.sqrt(2), rel_tol=0.05)


def test_agc_is_zero_at_the_floor() -> None:
    """A value at the noise floor gives 0, and a peak value gives 1."""
    assert dsp.agc(0.01, 0.0, 1.0, 0.01) == (0.0, 0.01)
    normalized, peak = dsp.agc(0.5, 0.2, 1.0, 0.01)
    assert (normalized, peak) == (1.0, 0.5)


def test_tempo_needs_enough_beats() -> None:
    """The tempo is 0 with too few beats in the window."""
    assert dsp.tempo((1.0, 1.5), 2.0) == 0
    assert math.isclose(dsp.tempo((1.0, 1.5, 2.0, 2.5), 2.5), 120)


def test_bass_bursts_over_other_sound_still_give_beats() -> None:
    """A steady mid tone and noise do not hide or add bass beats."""
    rng = np.random.default_rng(2)
    seconds = 4.0
    signal = (
        _bursts(60, period=0.5, length=0.1, seconds=seconds)
        + _tone(1000, seconds, 0.3)
        + rng.normal(0, 0.01, round(seconds * RATE))
    )
    last = _run(signal)[-1]
    assert last.beat_count == 8
    assert all(abs(b % 0.5) <= 2 * HOP for b in last.beats)
