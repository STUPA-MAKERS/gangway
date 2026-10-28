"""The `extrapolate` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)


def extrapolate(animation: AnimationOrColor, latency: float = 0.0) -> Animation:
    """Move each person along its velocity to hide the sensor latency.

    Args:
        animation: The sub-animation that gets the moved persons.
        latency: The time to look ahead in seconds.

    Returns:
        The animation.
    """
    last_object_state: dict[int, tuple[TrackedPoint, float]] = {}
    object_velocities: dict[int, TrackedPoint] = {}
    last_processed_instance: dict[int, int] = {}

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        current_objects = list(objects)
        predicted_objects: list[TrackedPoint] = []
        current_ids: set[int] = set()

        for obj in current_objects:
            obj_id = obj.id
            current_ids.add(obj_id)

            # The sensor receiver makes new point objects for each
            # measurement. The same object means the same measurement.
            pid = id(obj)
            if last_processed_instance.get(obj_id) != pid:
                obj_time = obj.timestamp
                prev_pos, prev_time = last_object_state.get(obj_id, (obj, obj_time))

                if obj_id not in last_object_state:
                    object_velocities[obj_id] = TrackedPoint(0, 0)
                else:
                    dt = obj_time - prev_time
                    if dt > 0.001:
                        object_velocities[obj_id] = (obj - prev_pos) / dt

                last_object_state[obj_id] = (obj, obj_time)
                last_processed_instance[obj_id] = pid

            vel = object_velocities.get(obj_id, TrackedPoint(0, 0))
            # Point subtraction is reversed (other - self), so a negative
            # factor moves the point forward along the velocity.
            predicted = obj + vel * latency * (-1)
            predicted_objects.append(TrackedPoint(predicted.x, predicted.y, id=obj.id))

        for k in list(last_object_state.keys()):
            if k not in current_ids:
                del last_object_state[k]
                object_velocities.pop(k, None)
                last_processed_instance.pop(k, None)

        if isinstance(animation, RGBCCT):
            return animation

        return animation(time, ctx, led, predicted_objects)

    return func
