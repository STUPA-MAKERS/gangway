"""The `audio_gain` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    AudioSource,
    SceneContext,
    TrackedPoint,
)
from ._frame import gain


def audio_gain(
    animation: AnimationOrColor,
    source: AudioSource = AudioSource.LEVEL,
    min_gain: float = 0.0,
    max_gain: float = 1.0,
) -> Animation:
    """Scale the brightness of an animation by an audio value.

    Args:
        animation: The animation to scale.
        source: The audio value that sets the gain.
        min_gain: The gain in silence.
        max_gain: The gain at the recent peak. A value above 1 makes the
            animation brighter, up to the channel limit of 255.

    Returns:
        The animation.
    """

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        color = render(animation, time, ctx, led, objects)
        factor = min_gain + (max_gain - min_gain) * ctx.audio.value(source)
        return color if factor == 1 else gain(color, max(factor, 0.0))

    return func
