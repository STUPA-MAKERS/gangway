"""The `beat_pulse` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
from ._frame import mix, per_frame


def beat_pulse(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255),
    background: AnimationOrColor = RGBCCT(),
    decay: float = 0.25,
) -> Animation:
    """Flash all LEDs on each beat and fade back to the background.

    Args:
        color: The color of the flash.
        background: The animation between the flashes.
        decay: The time constant of the exponential fade in seconds. After
            this time, the flash has 37 % of its strength.

    Returns:
        The animation.
    """
    tau = max(decay, 1e-6)

    def strength(time: float, ctx: SceneContext) -> float:
        age = max(time - ctx.audio.last_beat, 0.0)
        return math.exp(-age / tau)

    frame_strength = per_frame(strength)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        base = render(background, time, ctx, led, objects)
        return mix(color, base, frame_strength(time, ctx))

    return animation
