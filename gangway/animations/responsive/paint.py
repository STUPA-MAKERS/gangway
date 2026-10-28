"""The `paint` animation."""

from collections.abc import Sequence
from dataclasses import dataclass

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
from .._common import render_pair

_SAMPLE_RATE = 0.05
"""The time between two history samples in seconds.

A rate of 20 Hz keeps the history short enough to check for each LED in each
frame.
"""


@dataclass(frozen=True)
class _Trail:
    """The painted path at one frame.

    Attributes:
        history: The sampled positions as ``(x, y, time)``.
        frame_time: The time of the last frame update.
        sample_time: The time of the last sample.
        points: The positions that are lit in this frame.
    """

    history: tuple[tuple[float, float, float], ...] = ()
    frame_time: float = -1.0
    sample_time: float = -1.0
    points: tuple[tuple[float, float], ...] = ()


def _advance(
    trail: _Trail, time: float, objects: Sequence[TrackedPoint], persistence: float
) -> _Trail:
    """Get the trail of the next frame.

    The function drops the samples that are older than ``persistence`` and
    adds a sample of each person when the sample time is due. The lit
    points also include the current positions. Without them, a new person
    shows only at the next sample.
    """
    cutoff = time - persistence
    kept = tuple(h for h in trail.history if h[2] > cutoff)
    sample = time - trail.sample_time >= _SAMPLE_RATE
    history = kept + tuple((obj.x, obj.y, time) for obj in objects) if sample else kept
    return _Trail(
        history=history,
        frame_time=time,
        sample_time=time if sample else trail.sample_time,
        points=(
            *((x, y) for x, y, _ in history),
            *((obj.x, obj.y) for obj in objects),
        ),
    )


def paint(
    primary: AnimationOrColor = RGBCCT(r=255, g=0, b=0),
    secondary: AnimationOrColor = RGBCCT(r=0, g=0, b=0),
    radius: float = 150,
    persistence: float = 2.0,
) -> Animation:
    """Show ``primary`` around each person and along their recent path.

    This is like `dot`, but each position stays lit for ``persistence``
    seconds.

    Args:
        primary: The animation on the path.
        secondary: The animation outside the path.
        radius: The radius around each position.
        persistence: The time that a position stays lit in seconds.

    Returns:
        The animation. It keeps the path of the earlier frames as an
        immutable `_Trail` and replaces it on the first call of each frame.
        The animation gets one call for each LED, but the time changes only
        between frames. The hit test compares squared distances to save a
        square root for each point.
    """
    trail = _Trail()
    radius_sq = radius**2

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        nonlocal trail
        if time > trail.frame_time:
            trail = _advance(trail, time, objects, persistence)

        painted, background = render_pair(primary, secondary, time, ctx, led, objects)
        led_x, led_y = led.p.x, led.p.y
        hit = any(
            (led_x - px) ** 2 + (led_y - py) ** 2 < radius_sq for px, py in trail.points
        )
        return painted if hit else background

    return animation
