"""The `smooth` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)
from .._common import channels, from_channels

type _Color = tuple[float, ...]


def smooth(
    animation: AnimationOrColor,
    smoothing: float = 0.5,
) -> Animation:
    """Smooth an animation over time with an exponential moving average.

    Args:
        animation: The animation to smooth.
        smoothing: The weight of the previous color, from 0 to 1. 0 gives
            no smoothing. 1 keeps the first color forever.

    Returns:
        The animation. The average of each LED depends on its earlier
        frames, so the animation keeps one entry for each LED. The entries
        are floats, because integer channels would lose small steps.
    """
    weight = 1.0 - smoothing
    last_colors: dict[int, _Color] = {}

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        target = render(animation, time, ctx, led, objects)
        current = last_colors.get(led.index)
        if current is None:
            last_colors[led.index] = tuple(map(float, channels(target)))
            return target
        averaged = tuple(
            old * smoothing + new * weight
            for old, new in zip(current, channels(target), strict=True)
        )
        last_colors[led.index] = averaged
        return from_channels(averaged)

    return func
