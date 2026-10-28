"""The `smooth` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)

type _Color = tuple[float, float, float, float, float]


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
        The animation.
    """
    # Keep the state as floats. Integer channels would lose small steps.
    last_colors: dict[int, _Color] = {}

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        target = (
            animation
            if isinstance(animation, RGBCCT)
            else animation(time, ctx, led, objects)
        )

        current = last_colors.get(led.index)

        if current is None:
            last_colors[led.index] = (
                float(target.r),
                float(target.g),
                float(target.b),
                float(target.cw),
                float(target.ww),
            )
            return target

        weight = 1.0 - smoothing
        next_r = current[0] * smoothing + target.r * weight
        next_g = current[1] * smoothing + target.g * weight
        next_b = current[2] * smoothing + target.b * weight
        next_cw = current[3] * smoothing + target.cw * weight
        next_ww = current[4] * smoothing + target.ww * weight

        last_colors[led.index] = (next_r, next_g, next_b, next_cw, next_ww)

        return RGBCCT(
            r=int(next_r),
            g=int(next_g),
            b=int(next_b),
            cw=int(next_cw),
            ww=int(next_ww),
        )

    return func
