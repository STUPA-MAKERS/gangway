"""The `alternate` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)


def _off(
    _time: float,
    _ctx: SceneContext,
    _led: LED,
    _objects: Sequence[TrackedPoint],
) -> RGBCCT:
    return RGBCCT()


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
    if len(animations) == 0:
        return _off

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        anim = animations[int(time / length) % len(animations)]
        return anim if isinstance(anim, RGBCCT) else anim(time, ctx, led, objects)

    return animation
