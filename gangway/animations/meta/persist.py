"""The `persist` animation."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    SceneContext,
    TrackedPoint,
)

_GRACE = 0.1
"""The time in seconds that a person of an earlier frame stays without a match."""


@dataclass(frozen=True)
class _Memory:
    """The persons that `persist` keeps at one frame.

    Attributes:
        seen: The last position and the last time for each key.
        frame_time: The time of the last frame update.
        objects: The kept persons, in the order of the first sighting.
    """

    seen: Mapping[int, tuple[TrackedPoint, float]] = field(
        default_factory=dict[int, tuple[TrackedPoint, float]]
    )
    frame_time: float = -1.0
    objects: tuple[TrackedPoint, ...] = ()


def _remember(
    memory: _Memory, time: float, objects: Sequence[TrackedPoint], duration: float
) -> _Memory:
    """Get the memory of the next frame.

    The key is the hash of the position, not the track ID. A moving person
    gets a new key in each frame, so stale keys expire fast. The merge keeps
    the position of the known keys in the order, like an update in place.
    """
    current = {hash(obj.tuple): (obj, time) for obj in objects}
    merged = {**memory.seen, **current}
    seen = {
        key: (point, last_seen)
        for key, (point, last_seen) in merged.items()
        if not (
            time - last_seen > duration
            or (key not in current and time - last_seen > _GRACE)
        )
    }
    return _Memory(
        seen=seen,
        frame_time=time,
        objects=tuple(point for point, _last_seen in seen.values()),
    )


def persist(
    animation: Animation,
    duration: float = 2.0,
) -> Animation:
    """Keep persons alive for a sub-animation after they disappear.

    Args:
        animation: The sub-animation.
        duration: The maximum time to keep a person in seconds.

    Returns:
        The animation. It keeps the persons of the earlier frames as an
        immutable `_Memory` and replaces it on the first call of each frame.
        The animation gets one call for each LED, but the time changes only
        between frames.
    """
    memory = _Memory()

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        nonlocal memory
        if time > memory.frame_time:
            memory = _remember(memory, time, objects, duration)
        return animation(time, ctx, led, memory.objects)

    return func
