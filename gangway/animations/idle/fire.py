"""The `fire` animation."""

import random
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint
from .._common import scale


def fire(
    base_color: RGBCCT = RGBCCT(r=255, g=140, b=0),
    flicker_speed: float = 0.1,
    flicker_intensity: float = 0.5,
) -> Animation:
    """Flicker the brightness of a color at random, like a fire.

    Each LED uses a local random generator with a seed from its x position
    and the time step. This gives a repeatable flicker and does not change
    the global random state.

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
        seed = hash((led.p.x, int(time / flicker_speed)))
        return scale(base_color, 1.0 - flicker_intensity * random.Random(seed).random())

    return animation
