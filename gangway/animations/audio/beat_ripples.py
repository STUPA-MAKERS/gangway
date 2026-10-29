"""The `beat_ripples` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
from ._frame import mix, per_frame


def beat_ripples(
    color: RGBCCT = RGBCCT(b=255, g=128),
    background: AnimationOrColor = RGBCCT(),
    speed: float = 300.0,
    width: float = 40.0,
    max_radius: float = 300.0,
) -> Animation:
    """Send a ring out from each person on each beat.

    Args:
        color: The color of the rings.
        background: The animation behind the rings.
        speed: The speed of the ring radius in floor units per second.
        width: The distance from the ring line where the ring fades to the
            background, in floor units.
        max_radius: The radius where a ring ends. A ring fades as it grows.

    Returns:
        The animation. The rings move with the persons, because each frame
        draws them around the current positions.
    """
    half = max(width, 1e-6)
    end = max(max_radius, 1e-6)

    def rings(time: float, ctx: SceneContext) -> tuple[tuple[float, float], ...]:
        """Get the radius and the strength of each ring in the frame."""
        radii = (speed * (time - beat) for beat in ctx.audio.beats if time >= beat)
        return tuple((r, 1 - r / end) for r in radii if r < end)

    frame_rings = per_frame(rings)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        base = render(background, time, ctx, led, objects)
        active = frame_rings(time, ctx)
        if not active or not objects:
            return base
        x, y = led.p.x, led.p.y
        # A plain loop, because this runs for each LED, person and ring in
        # each frame, and a generator costs twice the time here.
        weight = 0.0
        for obj in objects:
            d = math.hypot(x - obj.x, y - obj.y)
            for radius, strength in active:
                off = abs(d - radius)
                if off < half:
                    weight = max(weight, strength * (1 - off / half))
        return mix(color, base, weight)

    return animation
