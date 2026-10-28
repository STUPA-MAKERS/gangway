"""The `strip_assignment` and `by_strip` animations."""

from collections.abc import Iterable, Sequence

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)


def strip_assignment(
    strip: int,
    animation: AnimationOrColor,
) -> tuple[int, AnimationOrColor]:
    """Assign an animation to a strip segment for `by_strip`.

    Args:
        strip: The position of the strip segment in the config.
        animation: The animation for the strip segment.

    Returns:
        The assignment.
    """
    return strip, animation


def by_strip(
    assignments: Iterable[tuple[int, AnimationOrColor]] | None = None,
    default: AnimationOrColor = RGBCCT(),
) -> Animation:
    """Show a different animation on each strip segment.

    Args:
        assignments: The animation for each strip segment, from
            `strip_assignment`.
        default: The animation for the strip segments with no assignment.

    Returns:
        The animation.
    """
    mapping = {} if assignments is None else dict(assignments)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        anim = mapping.get(led.strip_index, default)

        if isinstance(anim, RGBCCT):
            return anim
        return anim(time, ctx, led, objects)

    return animation
