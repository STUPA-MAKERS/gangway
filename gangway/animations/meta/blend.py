"""The `blend` animation."""

from collections.abc import Callable, Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    BlendMode,
    SceneContext,
    TrackedPoint,
)
from .._common import channels, dark


def _average(values: tuple[int, ...]) -> int:
    return int(sum(values) / len(values))


def _highest(values: tuple[int, ...]) -> int:
    return max(values)


def blend(
    *animations: AnimationOrColor, mode: BlendMode = BlendMode.AVERAGE
) -> Animation:
    """Mix the colors of animations channel by channel.

    Args:
        *animations: The animations to mix.
        mode: `BlendMode.AVERAGE` uses the mean of each channel.
            `BlendMode.MAX` uses the highest value of each channel.

    Returns:
        The animation. With no animations, all LEDs are off.
    """
    if not animations:
        return dark

    combine: Callable[[tuple[int, ...]], int] = (
        _highest if mode == BlendMode.MAX else _average
    )

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        colors = (render(anim, time, ctx, led, objects) for anim in animations)
        return RGBCCT(*map(combine, zip(*map(channels, colors), strict=True)))

    return animation
