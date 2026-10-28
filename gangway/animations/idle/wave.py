"""The `wave` animation."""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


@dataclass(frozen=True)
class _Wave:
    direction: tuple[float, float]
    color: RGBCCT
    phase: float


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
    waves: list[_Wave] = []
    for i in range(n_waves):
        angle = random.uniform(0, 2 * math.pi)
        direction = (math.cos(angle), math.sin(angle))
        color = random.choice(colors)
        waves.append(
            _Wave(direction=direction, color=color, phase=(i / n_waves) * 2 * math.pi)
        )

    k = 2 * math.pi / wavelength

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        r, g, b, cw, ww = 0.0, 0.0, 0.0, 0.0, 0.0

        for wave_params in waves:
            direction = wave_params.direction
            color = wave_params.color

            proj = led.p.x * direction[0] + led.p.y * direction[1]
            intensity = (
                1 + math.sin(k * proj - (k * speed * time) + wave_params.phase)
            ) / 2

            r += color.r * intensity
            g += color.g * intensity
            b += color.b * intensity
            cw += color.cw * intensity
            ww += color.ww * intensity

        return RGBCCT(
            r=min(255, int(r)),
            g=min(255, int(g)),
            b=min(255, int(b)),
            cw=min(255, int(cw)),
            ww=min(255, int(ww)),
        )

    return animation
