"""The `alternate` animation."""

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


def alternate(
    *animations: AnimationOrColor,
    length: float = 10,
) -> Animation:
    """Show each animation in turn.

    Args:
        *animations: The animations in the order to show them.
        length: The time for each animation in seconds.

    Returns:
        The animation. With no animations, all LEDs are off.
    """
    if not animations:
        return dark

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return render(
            animations[int(time / length) % len(animations)], time, ctx, led, objects
        )

    return animation
