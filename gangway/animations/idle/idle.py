"""The `idle` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint


def idle(
    idle_animation: AnimationOrColor, active_animation: AnimationOrColor
) -> Animation:
    """Select an animation from the presence of persons.

    Args:
        idle_animation: The animation when nobody is present.
        active_animation: The animation when one or more persons are present.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return render(
            active_animation if objects else idle_animation, time, ctx, led, objects
        )

    return animation
