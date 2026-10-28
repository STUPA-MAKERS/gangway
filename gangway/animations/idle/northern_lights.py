"""The `northern_lights` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def northern_lights(
    speed: float = 0.5,
    intensity: float = 0.8,
) -> Animation:
    """Show flowing curtains of green, teal and purple.

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

        dx = ctx.floor.p2.x - ctx.floor.p1.x
        dy = ctx.floor.p2.y - ctx.floor.p1.y
        x_norm = (led.p.x - ctx.floor.p1.x) / (dx if dx != 0 else 1.0)
        y_norm = (led.p.y - ctx.floor.p1.y) / (dy if dy != 0 else 1.0)

        v1 = math.sin(x_norm * 2.0 + t)
        v2 = math.sin(y_norm * 1.5 - t * 0.7 + v1)
        v3 = math.sin((x_norm + y_norm) * 3.0 + t * 1.5)

        # Green is the main color. Red and blue only add purple tints.
        r = (math.sin(v1 + t) * 0.5 + 0.5) * 50
        g = (math.sin(v2 + t * 0.5) * 0.5 + 0.5) * 200
        b = (math.sin(v3 - t) * 0.5 + 0.5) * 150

        return RGBCCT(
            r=int(r * intensity),
            g=int(g * intensity),
            b=int(b * intensity),
        )

    return animation
