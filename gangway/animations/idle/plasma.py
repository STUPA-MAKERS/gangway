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

    Note:
        The sum of the waves uses the ``+`` operator, not `sum`. Since
        Python 3.12, `sum` adds floats with compensation, and that can
        change the last bit of the hue.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        t = time * speed
        x, y = led.p.x, led.p.y
        cx = x + 0.5 * math.sin(t / 5.0)
        cy = y + 0.5 * math.cos(t / 3.0)
        v = (
            math.sin((x * scale) + t)
            + math.sin((y * scale) / 2.0 + t)
            + math.sin((x * scale + y * scale) / 2.0 + t)
            + math.sin(math.sqrt((cx * scale) ** 2 + (cy * scale) ** 2) + t)
        ) / 4.0
        return RGBCCT(*hsv_to_rgb((t + v) % 1.0, 1.0, 1.0))

    return animation
