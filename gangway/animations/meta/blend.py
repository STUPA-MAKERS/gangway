"""The `blend` animation."""

from collections.abc import Sequence
from typing import Literal

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)


def blend(
    *animations: AnimationOrColor, mode: Literal["average", "max"] = "average"
) -> Animation:
    """Mix the colors of animations channel by channel.

    Args:
        *animations: The animations to mix.
        mode: ``"average"`` uses the mean of each channel. ``"max"`` uses the
            highest value of each channel.

    Returns:
        The animation. With no animations, all LEDs are off.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        colors_list = [
            anim if isinstance(anim, RGBCCT) else anim(time, ctx, led, objects)
            for anim in animations
        ]

        if not colors_list:
            return RGBCCT()

        tuples = (
            (color.r, color.g, color.b, color.cw, color.ww) for color in colors_list
        )
        zipped = zip(*tuples, strict=True)

        if mode == "max":
            result = tuple(max(values) for values in zipped)
        else:
            result = tuple(int(sum(values) / len(colors_list)) for values in zipped)

        return RGBCCT(r=result[0], g=result[1], b=result[2], cw=result[3], ww=result[4])

    return animation
