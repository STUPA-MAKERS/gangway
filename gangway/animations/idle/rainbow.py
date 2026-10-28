"""The `rainbow` and `linear_rainbow` animations."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, Axis, SceneContext, TrackedPoint
from .._common import axis
from ._color import hsv_to_rgb


def _hue_color(position: float, spread: float, time: float, speed: float) -> RGBCCT:
    return RGBCCT(*hsv_to_rgb((position * spread + time * speed) % 1.0, 1.0, 1.0))


def rainbow(speed: float = 0.1, spread: float = 3.0) -> Animation:
    """Move a rainbow gradient along the x axis.

    Args:
        speed: The hue change per second.
        spread: The number of rainbows across the floor.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        width = (ctx.floor.p2.x - ctx.floor.p1.x) or 1.0
        x_norm = (led.p.x - ctx.floor.p1.x) / width
        return _hue_color(x_norm, spread, time, speed)

    return animation


def linear_rainbow(
    direction: Axis = Axis.X, speed: float = 0.1, spread: float = 3.0
) -> Animation:
    """Move a rainbow gradient along the x or y axis.

    Args:
        direction: The axis of the gradient.
        speed: The hue change per second.
        spread: The number of rainbows across the floor.

    Returns:
        The animation.
    """
    coordinate = axis(direction)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        start = coordinate(ctx.floor.p1)
        length = (coordinate(ctx.floor.p2) - start) or 1.0
        return _hue_color((coordinate(led.p) - start) / length, spread, time, speed)

    return animation
