"""Tests for the render loop of the LED controller."""

import itertools
from unittest.mock import MagicMock

import pytest
from rpi_ws2805 import RGBCCT

from gangway import led_controller


def test_frame_rate_is_the_mean_of_the_last_100_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Old frames leave the mean: 50 slow frames, then 100 fast ones.

    §F/lighting/render/000044
    """
    monkeypatch.setattr(led_controller, "PixelStrip", MagicMock())
    controller = led_controller.LEDController()
    frame_times = [1.0] * 50 + [0.01] * 100
    ticks = itertools.accumulate([0.0, *frame_times])
    monkeypatch.setattr(led_controller.time, "perf_counter", lambda: next(ticks))
    frames = itertools.count(1)

    def apply(_colors: dict[int, RGBCCT]) -> None:
        if next(frames) == len(frame_times):
            controller.running = False

    monkeypatch.setattr(controller, "apply_colors", apply)

    controller.run()

    assert controller.fps == pytest.approx(100.0)
    assert controller.tpf_max == pytest.approx(0.01)
    assert controller.tpf_avg == pytest.approx(0.01)
