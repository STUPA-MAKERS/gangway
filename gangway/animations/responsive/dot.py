"""The `dot` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
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
        primary_rgbcct = (
            primary if isinstance(primary, RGBCCT) else primary(time, ctx, led, objects)
        )
        secondary_rgbcct = (
            secondary
            if isinstance(secondary, RGBCCT)
            else secondary(time, ctx, led, objects)
        )

        return (
            primary_rgbcct
            if any((led.p - obj).length < radius for obj in objects)
            else secondary_rgbcct
        )

    return animation
