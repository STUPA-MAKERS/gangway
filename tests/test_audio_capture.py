"""Tests for the capture thread, the device search and the audio settings."""

import logging
import threading
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager

import numpy as np
import pytest

from gangway.audio import (
    AudioCapture,
    AudioSettings,
    BlockSource,
    find_device,
    parse_settings,
)
from gangway.audio.dsp import Samples
from gangway.types import SILENT_AUDIO

RATE = 22050
BLOCK = 512


class _FakeSource:
    """Give prepared blocks, then wait for the test and fail like an unplug."""

    def __init__(self, blocks: list[Samples], drained: threading.Event) -> None:
        self._blocks = blocks
        self._drained = drained
        self.proceed = threading.Event()

    def read(self) -> Samples:
        if self._blocks:
            return self._blocks.pop(0)
        self._drained.set()
        _ = self.proceed.wait(5)
        msg = "device unplugged"
        raise RuntimeError(msg)


def _burst_blocks(seconds: float) -> list[Samples]:
    t = np.arange(round(seconds * RATE)) / RATE
    signal = np.where((t % 0.5) < 0.1, 0.5 * np.sin(2 * np.pi * 60 * t), 0.0)
    return [signal[i : i + BLOCK] for i in range(0, signal.size - BLOCK + 1, BLOCK)]


class _Opener:
    """Open the fake source once, then fail like a missing device."""

    def __init__(self, source: _FakeSource) -> None:
        self.source = source
        self.calls = 0
        self.failed = threading.Event()

    def __call__(self, _settings: AudioSettings) -> AbstractContextManager[BlockSource]:
        self.calls += 1
        return self._open()

    @contextmanager
    def _open(self) -> Generator[BlockSource]:
        if self.calls > 1:
            if self.calls > 3:
                self.failed.set()
            msg = "No input device matches 'AK5371'"
            raise OSError(msg)
        yield self.source


def test_capture_publishes_beats_and_survives_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The thread analyzes blocks, then goes silent and retries on errors."""
    drained = threading.Event()
    source = _FakeSource(_burst_blocks(2.0), drained)
    opener = _Opener(source)
    ticks = iter(range(10_000))
    capture = AudioCapture(
        AudioSettings(),
        open_stream=opener,
        clock=lambda: next(ticks) * BLOCK / RATE,
        retry_interval=0.01,
    )
    with caplog.at_level(logging.WARNING, logger="gangway.audio.capture"):
        capture.start()
        assert drained.wait(5)
        snapshot = capture.latest()
        assert capture.capturing
        assert snapshot.beat_count == 4
        assert snapshot.beats[0] == 0.0

        source.proceed.set()
        assert opener.failed.wait(5)
        assert capture.latest() is SILENT_AUDIO
        assert not capture.capturing
        capture.stop(timeout=5)

    assert not capture.is_alive()
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "device unplugged" in warnings[0].getMessage()


def test_capture_without_start_is_silent() -> None:
    """A thread that never starts gives the silent snapshot."""
    capture = AudioCapture(AudioSettings(enabled=False))
    assert capture.latest() is SILENT_AUDIO
    capture.stop()


def test_find_device_prefers_the_direct_hardware_device() -> None:
    """The search matches a part of the name and prefers an hw: device."""
    devices: list[dict[str, object]] = [
        {"name": "HDA Intel PCH: HDMI 0 (hw:0,3)", "max_input_channels": 0},
        {"name": "sysdefault:CARD=AK5371", "max_input_channels": 2},
        {"name": "AKM AK5371: USB Audio (hw:2,0)", "max_input_channels": 2},
        {"name": "AK5371 output", "max_input_channels": 0},
    ]
    assert find_device(devices, "ak5371") == 2
    assert find_device(devices[:2], "AK5371") == 1
    assert find_device(devices, "missing") is None
    assert find_device(devices, 7) == 7


def test_parse_settings_reads_the_section() -> None:
    """A missing section gives the defaults, and keys override them."""
    assert parse_settings(None) == AudioSettings()
    settings = parse_settings({"device": 3, "sample_rate": 44100, "noise_floor": 0})
    assert settings == AudioSettings(device=3, sample_rate=44100, noise_floor=0.0)


@pytest.mark.parametrize(
    ("section", "error"),
    [
        ({"enabled": "yes"}, TypeError),
        ({"block_size": True}, TypeError),
        ({"sample_rate": 0}, TypeError),
        ({"gain": 2}, ValueError),
    ],
)
def test_parse_settings_rejects_bad_values(
    section: dict[str, object], error: type[Exception]
) -> None:
    """A wrong type, a bad number or an unknown key raises an error."""
    with pytest.raises(error):
        _ = parse_settings(section)
