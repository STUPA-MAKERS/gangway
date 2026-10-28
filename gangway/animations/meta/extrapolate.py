"""The `extrapolate` animation."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import reduce

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)


@dataclass(frozen=True)
class _Track:
    """The last measurement of one person.

    Attributes:
        point: The last measured position.
        time: The time of the last measurement.
        velocity: The velocity, in the reversed direction of `Point.__sub__`.
        instance: The ``id()`` of the point object of the last measurement.
    """

    point: TrackedPoint
    time: float
    velocity: TrackedPoint
    instance: int


_MIN_DT = 0.001
"""The shortest time between two measurements that gives a new velocity."""

type _Tracks = Mapping[int, _Track]
type _Step = tuple[_Tracks, tuple[TrackedPoint, ...]]


def _observe(track: _Track | None, obj: TrackedPoint) -> _Track:
    """Update the track of a person with a measurement.

    The sensor receiver makes new point objects for each measurement. Thus
    the same object means the same measurement, and the track stays.
    """
    match track:
        case None:
            return _Track(obj, obj.timestamp, TrackedPoint(0, 0), id(obj))
        case _Track(instance=instance) if instance == id(obj):
            return track
        case _Track(point=point, time=time, velocity=velocity):
            dt = obj.timestamp - time
            return _Track(
                obj,
                obj.timestamp,
                (obj - point) / dt if dt > _MIN_DT else velocity,
                id(obj),
            )


def _predict(obj: TrackedPoint, velocity: TrackedPoint, latency: float) -> TrackedPoint:
    """Move a person forward along its velocity for ``latency`` seconds.

    Point subtraction is reversed (``other - self``), so a negative factor
    moves the point forward.
    """
    predicted = obj + velocity * latency * (-1)
    return TrackedPoint(predicted.x, predicted.y, id=obj.id)


def extrapolate(animation: AnimationOrColor, latency: float = 0.0) -> Animation:
    """Move each person along its velocity to hide the sensor latency.

    Args:
        animation: The sub-animation that gets the moved persons.
        latency: The time to look ahead in seconds.

    Returns:
        The animation. The velocity needs the measurement of an earlier
        frame, so the animation keeps the tracks of the visible persons.
        Each call replaces the mapping with a new one.
    """

    def step(acc: _Step, obj: TrackedPoint) -> _Step:
        """Add one person to the tracks and to the predictions.

        The fold adds the persons one by one. Thus a repeated ID sees the
        measurement before it, like a sequential update.
        """
        tracks, predicted = acc
        track = _observe(tracks.get(obj.id), obj)
        return (
            {**tracks, obj.id: track},
            (*predicted, _predict(obj, track.velocity, latency)),
        )

    tracks: _Tracks = {}

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        nonlocal tracks
        updated, predicted = reduce(step, objects, (tracks, ()))
        current_ids = {obj.id for obj in objects}
        tracks = {key: track for key, track in updated.items() if key in current_ids}
        return render(animation, time, ctx, led, predicted)

    return func
