"""The `northern_lights` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def _normalize(value: float, start: float, end: float) -> float:
    return (value - start) / ((end - start) or 1.0)


def _wave(value: float) -> float:
    return math.sin(value) * 0.5 + 0.5


def northern_lights(
    speed: float = 0.5,
    intensity: float = 0.8,
) -> Animation:
    """Show flowing curtains of green, teal and purple.

    Green is the main color. Red and blue only add purple tints.

    Args:
        speed: The speed of the flow.
        intensity: The brightness, from 0 to 1.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        t = time * speed
        x_norm = _normalize(led.p.x, ctx.floor.p1.x, ctx.floor.p2.x)
        y_norm = _normalize(led.p.y, ctx.floor.p1.y, ctx.floor.p2.y)

        v1 = math.sin(x_norm * 2.0 + t)
        v2 = math.sin(y_norm * 1.5 - t * 0.7 + v1)
        v3 = math.sin((x_norm + y_norm) * 3.0 + t * 1.5)

        return RGBCCT(
            r=int(_wave(v1 + t) * 50 * intensity),
            g=int(_wave(v2 + t * 0.5) * 200 * intensity),
            b=int(_wave(v3 - t) * 150 * intensity),
        )

    return animation
