"""The `beat_switch` animation."""

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
from .._common import dark


def beat_switch(
    *animations: AnimationOrColor,
    beats_per_switch: int = 4,
) -> Animation:
    """Show each animation in turn, with a step after a number of beats.

    Args:
        *animations: The animations in the order to show them.
        beats_per_switch: The number of beats for each animation.

    Returns:
        The animation. It selects the animation from the beat count of the
        sound snapshot, so it keeps no state, and silence holds the current
        animation. With no animations, all LEDs are off.
    """
    if not animations:
        return dark
    step = max(beats_per_switch, 1)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        index = (ctx.audio.beat_count // step) % len(animations)
        return render(animations[index], time, ctx, led, objects)

    return animation
