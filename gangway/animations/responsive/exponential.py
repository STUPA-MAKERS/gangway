"""The `exponential` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import interpolate_rgbcct
from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
from .._common import render_pair


def exponential(
    primary: AnimationOrColor = RGBCCT(r=255),
    secondary: AnimationOrColor = RGBCCT(g=255),
    radius: float = 150,
) -> Animation:
    """Fade from ``secondary`` to ``primary`` near the closest person.

    Args:
        primary: The animation at the position of a person.
        secondary: The animation far from all persons.
        radius: The distance that halves the weight of ``primary``.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        intensity = max(
            (2 ** (-(led.p - obj).length / radius) for obj in objects), default=0
        )
        near, far = render_pair(primary, secondary, time, ctx, led, objects)
        return interpolate_rgbcct(near, far, intensity, use_sign=False)

    return animation
