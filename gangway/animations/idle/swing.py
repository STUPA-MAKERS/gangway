"""The `swing` animation."""

import math
from collections.abc import Sequence
from typing import Literal

from rpi_ws2805 import RGBCCT

from ...helpers import interpolate_rgbcct
from ...types import LED, Animation, SceneContext, TrackedPoint


def swing(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255, cw=255),
    direction: Literal["x", "y"] = "y",
    wavelength: int = 50,
    speed: float = 10,
) -> Animation:
    """Move a band of light back and forth along an axis.

    Args:
        color: The color of the band.
        direction: The axis of the movement.
        wavelength: The distance that halves the brightness, in floor units.
        speed: The angular speed of the movement in radians per second.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        coordinate: float = led.p.x if direction == "x" else led.p.y
        floor_len: float = (
            ctx.floor.p2.x - ctx.floor.p1.x
            if direction == "x"
            else ctx.floor.p2.y - ctx.floor.p1.y
        )

        target_coordinate: float = (
            math.sin(time * speed) * floor_len / 2 + floor_len / 2
        )

        intensity = 2 ** (-abs(coordinate - target_coordinate) / wavelength)

        if intensity < 0.2:
            intensity = 0

        return interpolate_rgbcct(color, RGBCCT(), intensity, use_sign=False)

    return animation
