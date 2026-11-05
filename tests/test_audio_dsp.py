"""Tests for the sound analysis with synthetic signals."""

import math
from collections.abc import Iterable

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


def _run(signal: dsp.Samples, bass_gain: float = 1.0) -> list[AudioState]:
    """Feed a signal block by block and get the snapshot of each block."""
    params = dsp.make_params(RATE, BLOCK, bass_gain=bass_gain)
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


def test_bass_gain_lifts_quiet_bass_above_the_floor() -> None:
    """A quiet bass tone is silent without the gain and shows with it."""
    signal = _tone(60, 2.0, amplitude=0.008)
    plain = _run(signal)[-1]
    lifted = _run(signal, bass_gain=4.0)[-1]
    assert (plain.bass, plain.spectrum[0]) == (0, 0)
    assert lifted.bass > 0.2
    assert lifted.spectrum[0] > 0.2
    assert lifted.mid == 0


def test_bass_gain_only_scales_the_bass_bands() -> None:
    """The gain applies to the spectrum bands below the bass end only."""
    params = dsp.make_params(RATE, BLOCK, bass_gain=4.0)
    assert params.spectrum_gains == (4.0, 4.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)


def test_step_keeps_the_given_beats() -> None:
    """`step` keeps the beat times it gets and drops the old ones."""
    params = dsp.make_params(RATE, BLOCK)
    state = dsp.start(params)
    block = np.zeros(BLOCK)
    for now, beat in ((1.0, 0.98), (1.5, None), (2.0, 1.99), (12.0, 11.9)):
        state = dsp.step(params, state, block, now, beat)
    assert state.snapshot.beat_count == 3
    assert state.snapshot.beats == (11.9,)
    assert state.snapshot.last_beat == 11.9


def test_tempo_needs_enough_beats() -> None:
    """The tempo is 0 with too few beats in the window."""
    assert dsp.tempo((1.0, 1.5), 2.0) == 0
    assert math.isclose(dsp.tempo((1.0, 1.5, 2.0, 2.5), 2.5), 120)
