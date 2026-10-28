"""The `idle` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

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
        objects = list(objects)

        if len(objects) == 0:
            return (
                idle_animation
                if isinstance(idle_animation, RGBCCT)
                else idle_animation(time, ctx, led, objects)
            )
        return (
            active_animation
            if isinstance(active_animation, RGBCCT)
            else active_animation(time, ctx, led, objects)
        )

    return animation
