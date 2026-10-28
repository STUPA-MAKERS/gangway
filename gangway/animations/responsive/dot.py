"""The `dot` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
from .._common import render_pair
from ..idle import wave

_DOT_PRIMARY = wave([RGBCCT(r=255)])


_DOT_SECONDARY = wave([RGBCCT(g=255)])


def dot(
    primary: AnimationOrColor = _DOT_PRIMARY,
    secondary: AnimationOrColor = _DOT_SECONDARY,
    radius: float = 150,
) -> Animation:
    """Show ``primary`` in a circle around each person.

    Args:
        primary: The animation inside the circles.
        secondary: The animation outside the circles.
        radius: The radius of the circles.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        inside, outside = render_pair(primary, secondary, time, ctx, led, objects)
        return (
            inside if any((led.p - obj).length < radius for obj in objects) else outside
        )

    return animation
