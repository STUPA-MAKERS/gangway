"""The `persist` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    SceneContext,
    TrackedPoint,
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
        The animation.
    """
    persisted_objects: dict[int, tuple[TrackedPoint, float]] = {}
    last_frame_time = -1.0

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        nonlocal last_frame_time

        # The function runs once for each LED, but the time only changes
        # between frames. Update the persons only on the first call of a frame.
        if time > last_frame_time:
            # The key is the hash of the position, not the track ID. A moving
            # person gets a new key in each frame, so stale keys expire fast.
            current_ids = {hash(o.tuple) for o in objects}
            for obj in objects:
                persisted_objects[hash(obj.tuple)] = (obj, time)

            expired_ids: list[int] = []
            for obj_id, (_point, last_seen) in persisted_objects.items():
                if time - last_seen > duration or (
                    obj_id not in current_ids and time - last_seen > 0.1
                ):
                    expired_ids.append(obj_id)

            for obj_id in expired_ids:
                persisted_objects.pop(obj_id, None)

            last_frame_time = time

        all_objects = [p for p, _t in persisted_objects.values()]
        return animation(time, ctx, led, all_objects)

    return func
