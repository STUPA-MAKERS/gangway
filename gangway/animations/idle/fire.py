"""The `fire` animation."""

import random
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def fire(
    base_color: RGBCCT = RGBCCT(r=255, g=140, b=0),
    flicker_speed: float = 0.1,
    flicker_intensity: float = 0.5,
) -> Animation:
    """Flicker the brightness of a color at random, like a fire.

    Args:
        base_color: The color at full brightness.
        flicker_speed: The time between two brightness changes in seconds.
        flicker_intensity: The maximum brightness decrease, from 0 to 1.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        time_bucket = int(time / flicker_speed)
        seed = hash((led.p.x, time_bucket))
        rand_gen = random.Random(seed)
        brightness_factor = 1.0 - flicker_intensity * rand_gen.random()

        return RGBCCT(
            r=int(base_color.r * brightness_factor),
            g=int(base_color.g * brightness_factor),
            b=int(base_color.b * brightness_factor),
            cw=int(base_color.cw * brightness_factor),
            ww=int(base_color.ww * brightness_factor),
        )

    return animation
