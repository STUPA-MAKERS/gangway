"""The `sparkle` animation."""

import random
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def sparkle(density: float = 0.1, speed: float = 20.0) -> Animation:
    """Light random LEDs in random colors.

    Args:
        density: The part of the LEDs that are lit, from 0 to 1.
        speed: The number of changes per second.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        seed = hash((led.index, int(time * speed)))
        rng = random.Random(seed)
        if rng.random() < density:
            return RGBCCT(
                r=rng.randint(0, 255),
                g=rng.randint(0, 255),
                b=rng.randint(0, 255),
            )
        return RGBCCT()

    return animation
