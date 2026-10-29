"""Pure functions that turn blocks of samples into `AudioState` snapshots.

The analysis is a fold: `step` takes the state of the earlier blocks and one
new block, and returns the next state. No function here keeps state or reads
a device, so the tests can feed synthetic signals.

The functions use these methods:

- The level is the RMS of the block.
- The bands come from a Hann-windowed FFT over the last `DspParams.fft_size`
  samples. Each band value is the RMS of the signal part in that band.
- Each value goes through an automatic gain control (AGC). The reference is
  the recent peak of the value. The peak follows a rise at once and halves
  every `AGC_HALF_LIFE` seconds. A noise floor keeps silence at 0.
- A beat is an onset in the bass band: the rise of the bass value from the
  last block (the flux) is larger than the mean plus `ONSET_K` standard
  deviations of the flux over the last `FLUX_WINDOW` seconds. A beat cannot
  follow the last beat in less than `REFRACTORY` seconds.
"""

import math
import statistics
from dataclasses import dataclass, replace
from itertools import pairwise

import numpy as np
from numpy.typing import NDArray

from ..types import SILENT_AUDIO, AudioState

type Samples = NDArray[np.float64]
"""Mono samples with values from -1 to 1."""

BASS_HZ = (40.0, 150.0)
"""The frequency range of the bass band in hertz."""

MID_HZ = (150.0, 2000.0)
"""The frequency range of the mid band in hertz."""

TREBLE_HZ = (2000.0, 8000.0)
"""The frequency range of the treble band in hertz."""

SPECTRUM_BANDS = 8
"""The number of bands in `AudioState.spectrum`.

The bands divide the range from the bass start to the treble end into
parts of equal width on a logarithmic scale.
"""

AGC_HALF_LIFE = 5.0
"""The time in seconds that halves the AGC peak when the sound gets quieter."""

MIN_RANGE = 4.0
"""The lowest AGC reference as a multiple of the noise floor.

Without this limit, a quiet room makes the peak decay to the noise. Then
the noise itself gives values near 1.
"""

FLUX_WINDOW = 1.0
"""The time in seconds of the flux history for the onset threshold."""

ONSET_K = 1.5
"""The number of standard deviations above the mean flux for a beat."""

MIN_ONSET = 0.1
"""The smallest flux for a beat, as a part of the AGC reference of the bass.

The adaptive threshold alone triggers on very small changes after a long
steady sound, because the standard deviation is then near 0.
"""

REFRACTORY = 0.25
"""The shortest time in seconds between two beats."""

BEAT_HISTORY = 10.0
"""The time in seconds that a beat stays in `AudioState.beats`."""

MAX_BEATS = 64
"""The largest number of beats in `AudioState.beats`."""

TEMPO_WINDOW = 8.0
"""The time in seconds of the beats that give the tempo."""

MIN_TEMPO_BEATS = 4
"""The smallest number of beats in `TEMPO_WINDOW` for a tempo."""


@dataclass(frozen=True, eq=False)
class DspParams:
    """The constants of one analysis, computed once for each stream.

    Attributes:
        sample_rate: The sample rate in hertz.
        block_size: The number of samples in a block.
        fft_size: The number of samples in the FFT window.
        noise_floor: The RMS value that counts as silence.
        window: The Hann window.
        norm: The factor that turns a band power sum into a mean square.
        bands: The ``(start, stop)`` FFT bins of bass, mid and treble.
        spectrum: The ``(start, stop)`` FFT bins of the spectrum bands.
        flux_len: The number of blocks in the flux history.
    """

    sample_rate: int
    block_size: int
    fft_size: int
    noise_floor: float
    window: Samples
    norm: float
    bands: tuple[tuple[int, int], ...]
    spectrum: tuple[tuple[int, int], ...]
    flux_len: int


def _bins(lo: float, hi: float, bin_hz: float, n_bins: int) -> tuple[int, int]:
    """Get the FFT bins of a frequency range.

    The range always gets one bin or more, so a coarse FFT cannot give an
    empty band.
    """
    start = min(max(1, math.ceil(lo / bin_hz)), n_bins - 1)
    stop = min(max(start + 1, math.ceil(hi / bin_hz)), n_bins)
    return start, stop


def make_params(
    sample_rate: int = 22050, block_size: int = 512, noise_floor: float = 0.01
) -> DspParams:
    """Compute the constants of an analysis.

    Args:
        sample_rate: The sample rate in hertz.
        block_size: The number of samples in a block.
        noise_floor: The RMS value that counts as silence, as a part of the
            full scale.

    Returns:
        The constants. The FFT window holds two blocks. This doubles the
        frequency resolution, which the narrow bass band needs.
    """
    fft_size = 2 * block_size
    window = np.hanning(fft_size)
    bin_hz = sample_rate / fft_size
    n_bins = fft_size // 2 + 1
    lo, hi = BASS_HZ[0], TREBLE_HZ[1]
    edges = [lo * (hi / lo) ** (i / SPECTRUM_BANDS) for i in range(SPECTRUM_BANDS + 1)]
    return DspParams(
        sample_rate=sample_rate,
        block_size=block_size,
        fft_size=fft_size,
        noise_floor=noise_floor,
        window=window,
        # A sine of RMS value A in a band gives a one-sided power sum of
        # A^2 * fft_size * sum(window^2) / 2, so this factor gives A^2.
        norm=2.0 / (fft_size * float(np.sum(window**2))),
        bands=tuple(
            _bins(a, b, bin_hz, n_bins) for a, b in (BASS_HZ, MID_HZ, TREBLE_HZ)
        ),
        spectrum=tuple(_bins(a, b, bin_hz, n_bins) for a, b in pairwise(edges)),
        flux_len=max(1, round(FLUX_WINDOW * sample_rate / block_size)),
    )


@dataclass(frozen=True, eq=False)
class Analysis:
    """The state of the analysis after one block.

    Attributes:
        frame: The last `DspParams.fft_size` samples.
        level_peak: The AGC peak of the level.
        band_peaks: The AGC peaks of bass, mid and treble.
        spectrum_peaks: The AGC peaks of the spectrum bands.
        prev_bass: The bass value of the last block, before the AGC.
        flux: The flux history, oldest first.
        beats: The recent beat times, oldest first.
        beat_count: The number of beats since the start.
        snapshot: The result for the animations.
    """

    frame: Samples
    level_peak: float = 0.0
    band_peaks: tuple[float, ...] = (0.0, 0.0, 0.0)
    spectrum_peaks: tuple[float, ...] = ()
    prev_bass: float = 0.0
    flux: tuple[float, ...] = ()
    beats: tuple[float, ...] = ()
    beat_count: int = 0
    snapshot: AudioState = SILENT_AUDIO


def start(params: DspParams) -> Analysis:
    """Get the state before the first block.

    Args:
        params: The constants of the analysis.

    Returns:
        The state with a silent window.
    """
    return Analysis(
        frame=np.zeros(params.fft_size),
        spectrum_peaks=(0.0,) * len(params.spectrum),
    )


def rms(samples: Samples) -> float:
    """Get the root mean square of samples.

    Args:
        samples: The samples.

    Returns:
        The RMS value, or 0 for no samples.
    """
    return math.sqrt(float(np.mean(samples**2))) if samples.size else 0.0


def band_values(
    params: DspParams, frame: Samples, bands: tuple[tuple[int, int], ...]
) -> tuple[float, ...]:
    """Get the RMS value of the signal in each band.

    Args:
        params: The constants of the analysis.
        frame: `DspParams.fft_size` samples.
        bands: The ``(start, stop)`` FFT bins of each band.

    Returns:
        The values in the order of ``bands``.
    """
    power = np.abs(np.fft.rfft(frame * params.window)) ** 2
    cumulative = np.concatenate(([0.0], np.cumsum(power)))
    return tuple(
        math.sqrt(params.norm * float(cumulative[stop] - cumulative[begin]))
        for begin, stop in bands
    )


def agc(value: float, peak: float, decay: float, floor: float) -> tuple[float, float]:
    """Normalize a value by its recent peak.

    Args:
        value: The new value.
        peak: The peak of the earlier values.
        decay: The factor that the peak decays by since the last value.
        floor: The value that counts as silence.

    Returns:
        The normalized value from 0 to 1, and the new peak.
    """
    new_peak = max(value, peak * decay)
    reference = max(new_peak, floor * MIN_RANGE)
    return min(max((value - floor) / (reference - floor), 0.0), 1.0), new_peak


def _agc_all(
    values: tuple[float, ...], peaks: tuple[float, ...], decay: float, floor: float
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    results = tuple(
        agc(value, peak, decay, floor)
        for value, peak in zip(values, peaks, strict=True)
    )
    return tuple(n for n, _ in results), tuple(p for _, p in results)


def is_onset(
    flux: float, history: tuple[float, ...], reference: float, since_beat: float
) -> bool:
    """Check if a bass flux is a beat.

    Args:
        flux: The rise of the bass value from the last block.
        history: The flux of the earlier blocks.
        reference: The AGC reference of the bass value.
        since_beat: The time since the last beat in seconds.

    Returns:
        True if the flux is above the adaptive threshold and above the
        minimum, and the refractory period is over.
    """
    mean = statistics.fmean(history) if history else 0.0
    std = statistics.pstdev(history, mean) if len(history) > 1 else 0.0
    return (
        since_beat >= REFRACTORY
        and flux > mean + ONSET_K * std
        and flux > MIN_ONSET * reference
    )


def tempo(beats: tuple[float, ...], now: float) -> float:
    """Estimate the tempo from the recent beats.

    Args:
        beats: The beat times, oldest first.
        now: The current time.

    Returns:
        The tempo in beats per minute from the median beat interval, or 0
        if `TEMPO_WINDOW` holds fewer than `MIN_TEMPO_BEATS` beats.
    """
    recent = [t for t in beats if now - t <= TEMPO_WINDOW]
    if len(recent) < MIN_TEMPO_BEATS:
        return 0.0
    return 60.0 / statistics.median(b - a for a, b in pairwise(recent))


def step(params: DspParams, state: Analysis, block: Samples, now: float) -> Analysis:
    """Analyze one block.

    Args:
        params: The constants of the analysis.
        state: The state after the earlier blocks.
        block: The new mono samples.
        now: The time of the block in seconds.

    Returns:
        The new state. Its `Analysis.snapshot` holds the result.
    """
    frame = np.concatenate((state.frame, block))[-params.fft_size :]
    decay = 0.5 ** (block.size / params.sample_rate / AGC_HALF_LIFE)
    floor = params.noise_floor

    level, level_peak = agc(rms(block), state.level_peak, decay, floor)
    raw_bands = band_values(params, frame, params.bands)
    bands, band_peaks = _agc_all(raw_bands, state.band_peaks, decay, floor)
    spectrum, spectrum_peaks = _agc_all(
        band_values(params, frame, params.spectrum), state.spectrum_peaks, decay, floor
    )

    bass = raw_bands[0]
    flux = max(bass - state.prev_bass, 0.0)
    last_beat = state.beats[-1] if state.beats else -math.inf
    beat = is_onset(
        flux, state.flux, max(band_peaks[0], floor * MIN_RANGE), now - last_beat
    )
    beats = tuple(
        t for t in (*state.beats, *((now,) if beat else ())) if now - t <= BEAT_HISTORY
    )[-MAX_BEATS:]
    beat_count = state.beat_count + beat

    return replace(
        state,
        frame=frame,
        level_peak=level_peak,
        band_peaks=band_peaks,
        spectrum_peaks=spectrum_peaks,
        prev_bass=bass,
        flux=(*state.flux, flux)[-params.flux_len :],
        beats=beats,
        beat_count=beat_count,
        snapshot=AudioState(
            level=level,
            bass=bands[0],
            mid=bands[1],
            treble=bands[2],
            spectrum=spectrum,
            last_beat=beats[-1] if beats else -math.inf,
            beats=beats,
            beat_count=beat_count,
            tempo=tempo(beats, now),
        ),
    )
