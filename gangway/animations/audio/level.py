"""The `level` animation."""

from collections.abc import Sequence
from dataclasses import dataclass

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    AudioSource,
    Axis,
    SceneContext,
    TrackedPoint,
)
from .._common import axis
from ._frame import extent, per_frame

_MIN_PEAK = 0.01
"""The lowest peak value that shows the peak dot.

Without this limit, the dot stays at the start of the axis in silence.
"""


@dataclass(frozen=True)
class _Meter:
    """The meter at one frame, in floor units along the axis.

    Attributes:
        time: The time of the frame.
        origin: The coordinate of the start of the axis.
        fill: The length of the filled part.
        peak: The held peak, from 0 to 1.
        peak_at: The distance of the peak dot from the origin.
    """

    time: float = -1.0
    origin: float = 0.0
    fill: float = 0.0
    peak: float = 0.0
    peak_at: float = 0.0


def _next_peak(meter: _Meter, time: float, value: float, fall: float) -> float:
    """Get the held peak of the next frame.

    A time before the last frame means that the timeline started again, so
    the peak starts from the value.
    """
    if time < meter.time:
        return value
    return max(value, meter.peak - fall * (time - meter.time))


def level(
    color: RGBCCT = RGBCCT(g=255),
    peak_color: RGBCCT = RGBCCT(r=255),
    background: AnimationOrColor = RGBCCT(),
    direction: Axis = Axis.Y,
    reverse: bool = False,
    source: AudioSource = AudioSource.LEVEL,
    peak_fall: float = 0.5,
    peak_width: float = 15.0,
) -> Animation:
    """Show a VU meter: a bar along an axis with a peak-hold dot.

    Args:
        color: The color of the bar.
        peak_color: The color of the peak dot.
        background: The animation outside the bar.
        direction: The axis of the bar.
        reverse: Set to True to start the bar at the high end of the axis.
        source: The audio value that sets the bar length.
        peak_fall: The speed of the falling peak dot, as a part of the
            floor length per second.
        peak_width: The width of the peak dot in floor units.

    Returns:
        The animation. The dot falls from the highest recent value, so the
        animation keeps the meter of the last frame.
    """
    coord = axis(direction)
    sign = -1.0 if reverse else 1.0
    half = peak_width / 2
    meter = _Meter()

    def advance(time: float, ctx: SceneContext) -> _Meter:
        nonlocal meter
        lo, hi = extent(ctx.floor, direction)
        value = ctx.audio.value(source)
        peak = _next_peak(meter, time, value, peak_fall)
        meter = _Meter(
            time=time,
            origin=hi if reverse else lo,
            fill=value * (hi - lo),
            peak=peak,
            peak_at=peak * (hi - lo),
        )
        return meter

    frame_meter = per_frame(advance)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        current = frame_meter(time, ctx)
        # The background renders for each LED, so that a stateful background
        # sees the same calls in each frame.
        base = render(background, time, ctx, led, objects)
        d = sign * (coord(led.p) - current.origin)
        if current.peak >= _MIN_PEAK and abs(d - current.peak_at) <= half:
            return peak_color
        return color if 0 <= d <= current.fill else base

    return animation
