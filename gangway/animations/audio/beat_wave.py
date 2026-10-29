"""The `beat_wave` animation."""

import math
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import LED, Animation, AnimationOrColor, Axis, SceneContext, TrackedPoint
from .._common import axis
from ._frame import extent, mix, per_frame


def beat_wave(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255),
    background: AnimationOrColor = RGBCCT(),
    direction: Axis = Axis.Y,
    reverse: bool = False,
    speed: float = 400.0,
    width: float = 80.0,
) -> Animation:
    """Send a wave front across the floor on each beat.

    Each front starts at one side of the floor and moves to the other side.
    It has a sharp leading edge and a tail that fades over ``width``. The
    front ends when its tail leaves the floor. Many fronts can move at the
    same time.

    Args:
        color: The color of the front.
        background: The animation behind the fronts.
        direction: The axis of the movement.
        reverse: Set to True to start at the high end of the axis.
        speed: The speed of a front in floor units per second.
        width: The length of the tail in floor units.

    Returns:
        The animation. It computes the front positions from the recent beat
        times once per frame, so it keeps no state of its own.
    """
    coord = axis(direction)
    sign = -1.0 if reverse else 1.0
    tail = max(width, 1e-6)

    def fronts(time: float, ctx: SceneContext) -> tuple[float, ...]:
        lo, hi = extent(ctx.floor, direction)
        origin = hi if reverse else lo
        lifetime = (hi - lo + tail) / speed if speed > 0 else math.inf
        return tuple(
            origin + sign * speed * (time - beat)
            for beat in ctx.audio.beats
            if 0 <= time - beat < lifetime
        )

    frame_fronts = per_frame(fronts)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        base = render(background, time, ctx, led, objects)
        u = coord(led.p)
        behind = (sign * (front - u) for front in frame_fronts(time, ctx))
        weight = max((1 - d / tail for d in behind if 0 <= d < tail), default=0.0)
        return mix(color, base, weight)

    return animation
