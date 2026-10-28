"""The `swing` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import interpolate_rgbcct
from ...types import LED, Animation, Axis, SceneContext, TrackedPoint
from .._common import axis

_CUTOFF = 0.2
"""The intensity below which the LED is off. This gives the band a sharp edge."""


def swing(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255, cw=255),
    direction: Axis = Axis.Y,
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
    coordinate = axis(direction)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        floor_len = coordinate(ctx.floor.p2) - coordinate(ctx.floor.p1)
        target = math.sin(time * speed) * floor_len / 2 + floor_len / 2
        intensity = 2 ** (-abs(coordinate(led.p) - target) / wavelength)
        return interpolate_rgbcct(
            color, RGBCCT(), 0 if intensity < _CUTOFF else intensity, use_sign=False
        )

    return animation
