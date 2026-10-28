"""The `rainbow` and `linear_rainbow` animations."""

from collections.abc import Sequence
from typing import Literal

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint
from ._color import hsv_to_rgb


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
        x_norm = (led.p.x - ctx.floor.p1.x) / (ctx.floor.p2.x - ctx.floor.p1.x)
        hue = (x_norm * spread + time * speed) % 1.0
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        return RGBCCT(r=r, g=g, b=b)

    return animation


def linear_rainbow(
    direction: Literal["x", "y"] = "x", speed: float = 0.1, spread: float = 3.0
) -> Animation:
    """Move a rainbow gradient along the x or y axis.

    Args:
        direction: The axis of the gradient.
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
        if direction == "x":
            pos = led.p.x
            min_p = ctx.floor.p1.x
            max_p = ctx.floor.p2.x
        else:
            pos = led.p.y
            min_p = ctx.floor.p1.y
            max_p = ctx.floor.p2.y

        length = max_p - min_p
        if length == 0:
            length = 1.0

        x_norm = (pos - min_p) / length
        hue = (x_norm * spread + time * speed) % 1.0
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        return RGBCCT(r=r, g=g, b=b)

    return animation
