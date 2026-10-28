"""The `exponential_at` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import interpolate_rgbcct
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)
from .._common import render_pair


def exponential_at(
    primary: AnimationOrColor = RGBCCT(r=255),
    secondary: AnimationOrColor = RGBCCT(g=255),
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 150,
) -> Animation:
    """Fade from ``secondary`` to ``primary`` near a fixed point.

    This is like `gangway.animations.responsive.exponential`, but the
    distance is to a fixed point, not to the persons.

    Args:
        primary: The animation at the point.
        secondary: The animation far from the point.
        x: The x coordinate of the point.
        y: The y coordinate of the point.
        radius: The distance that halves the weight of ``primary``.

    Returns:
        The animation.
    """
    target_point = TrackedPoint(x=x, y=y)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        near, far = render_pair(primary, secondary, time, ctx, led, objects)
        return interpolate_rgbcct(
            near,
            far,
            2 ** (-(led.p - target_point).length / radius),
            use_sign=False,
        )

    return animation
