"""The `sparkle` animation."""

import random
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def sparkle(density: float = 0.1, speed: float = 20.0) -> Animation:
    """Light random LEDs in random colors.

    Each LED uses a local random generator with a seed from the LED and the
    time step. This gives a repeatable pattern and does not change the
    global random state.

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
        rng = random.Random(hash((led.index, int(time * speed))))
        return (
            RGBCCT(*(rng.randint(0, 255) for _channel in range(3)))
            if rng.random() < density
            else RGBCCT()
        )

    return animation
