"""The `plasma` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint
from ._color import hsv_to_rgb


def plasma(speed: float = 0.5, scale: float = 0.05) -> Animation:
    """Show a plasma effect from a sum of sine waves.

    Args:
        speed: The speed of the effect.
        scale: The spatial frequency of the waves.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        t = time * speed
        v = 0.0
        v += math.sin((led.p.x * scale) + t)
        v += math.sin((led.p.y * scale) / 2.0 + t)
        v += math.sin((led.p.x * scale + led.p.y * scale) / 2.0 + t)
        cx = led.p.x + 0.5 * math.sin(t / 5.0)
        cy = led.p.y + 0.5 * math.cos(t / 3.0)
        v += math.sin(math.sqrt((cx * scale) ** 2 + (cy * scale) ** 2) + t)
        v /= 4.0

        hue = (t + v) % 1.0
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        return RGBCCT(r=r, g=g, b=b)

    return animation
