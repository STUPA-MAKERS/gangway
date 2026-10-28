"""The `wave` animation."""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from functools import reduce

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint
from .._common import Channels, channels

type _Totals = tuple[float, float, float, float, float]


@dataclass(frozen=True)
class _Wave:
    direction: tuple[float, float]
    channels: Channels
    phase: float


def _random_wave(index: int, n_waves: int, colors: Sequence[RGBCCT]) -> _Wave:
    """Make one wave from the global random generator.

    The function draws the angle before the color. This order of the
    random calls gives the same waves for the same seed.
    """
    angle = random.uniform(0, 2 * math.pi)
    return _Wave(
        direction=(math.cos(angle), math.sin(angle)),
        channels=channels(random.choice(colors)),
        phase=(index / n_waves) * 2 * math.pi,
    )


def _add(totals: _Totals, contribution: tuple[Channels, float]) -> _Totals:
    """Add the channels of one wave, scaled by its intensity, to the totals."""
    color, intensity = contribution
    r, g, b, cw, ww = totals
    return (
        r + color[0] * intensity,
        g + color[1] * intensity,
        b + color[2] * intensity,
        cw + color[3] * intensity,
        ww + color[4] * intensity,
    )


def wave(
    colors: list[RGBCCT],
    n_waves: int = 3,
    speed: float = 50.0,
    wavelength: float = 200.0,
) -> Animation:
    """Add up plane waves that move in random directions.

    Args:
        colors: The colors to select from. Each wave gets a random color.
        n_waves: The number of waves.
        speed: The speed of the waves in floor units per second.
        wavelength: The wavelength in floor units.

    Returns:
        The animation.
    """
    waves = tuple(_random_wave(i, n_waves, colors) for i in range(n_waves))
    k = 2 * math.pi / wavelength

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        shift = k * speed * time
        contributions = (
            (
                w.channels,
                (
                    1
                    + math.sin(
                        k * (led.p.x * w.direction[0] + led.p.y * w.direction[1])
                        - shift
                        + w.phase
                    )
                )
                / 2,
            )
            for w in waves
        )
        totals = reduce(_add, contributions, (0.0, 0.0, 0.0, 0.0, 0.0))
        return RGBCCT(*(min(255, int(total)) for total in totals))

    return animation
