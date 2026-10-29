"""The `paint` animation."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
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
        hits: Whether each LED of the scene is near a lit position, by LED
            index.
    """

    history: tuple[tuple[float, float, float], ...] = ()
    frame_time: float = -1.0
    sample_time: float = -1.0
    points: tuple[tuple[float, float], ...] = ()
    hits: Mapping[int, bool] = field(default_factory=dict[int, bool])


def _since(trail: _Trail, time: float) -> _Trail:
    """Get the trail that a frame at ``time`` builds on.

    A time before the last frame means that the timeline started again, for
    example after a config reload. The painted path then lies in a future
    that did not happen, so the trail starts empty.
    """
    return trail if time > trail.frame_time else _Trail()


def _hits(
    leds: Sequence[LED], points: Sequence[tuple[float, float]], radius_sq: float
) -> Mapping[int, bool]:
    """Test all LEDs against all lit positions in one array operation.

    The test for one LED in Python costs one loop step for each position.
    With many persons and a long history, that loop is most of the frame
    time, so the frame tests all pairs at once.
    """
    if not leds:
        return {}
    if not points:
        return dict.fromkeys((led.index for led in leds), False)
    led_xy = np.array([(led.p.x, led.p.y) for led in leds])
    point_xy = np.array(points)
    dist_sq = ((led_xy[:, None, :] - point_xy[None, :, :]) ** 2).sum(axis=2)
    near = (dist_sq < radius_sq).any(axis=1)
    return dict(zip((led.index for led in leds), near.tolist(), strict=True))


def _advance(
    trail: _Trail,
    time: float,
    objects: Sequence[TrackedPoint],
    persistence: float,
    leds: Sequence[LED],
    radius_sq: float,
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
    points = (
        *((x, y) for x, y, _ in history),
        *((obj.x, obj.y) for obj in objects),
    )
    return _Trail(
        history=history,
        frame_time=time,
        sample_time=time if sample else trail.sample_time,
        points=points,
        hits=_hits(leds, points, radius_sq),
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
        between frames. The first call of a frame tests all LEDs of the
        scene. An LED that is not in the scene gets its own test. The hit
        test compares squared distances to save a square root for each
        point.
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
        if time != trail.frame_time:
            trail = _advance(
                _since(trail, time), time, objects, persistence, ctx.leds, radius_sq
            )

        painted, background = render_pair(primary, secondary, time, ctx, led, objects)
        hit = trail.hits.get(led.index)
        if hit is None:
            led_x, led_y = led.p.x, led.p.y
            hit = any(
                (led_x - px) ** 2 + (led_y - py) ** 2 < radius_sq
                for px, py in trail.points
            )
        return painted if hit else background

    return animation
