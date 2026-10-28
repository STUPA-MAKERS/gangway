"""Animations that combine or change other animations."""

import datetime
from collections.abc import Iterable, Sequence
from typing import Literal

import yaml
from rpi_ws2805 import RGBCCT

from ..helpers import as_animation, interpolate_rgbcct, parse_animation
from ..types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
    YamlValue,
)

type _Color = tuple[float, float, float, float, float]
type SpeedMode = Literal["speed up", "slow down"]
"""The direction of the time change of `proximity_speed`."""

type _SpeedKey = tuple[tuple[float, float], SpeedMode, float, float, float, float]


def _off(
    _time: float,
    _ctx: SceneContext,
    _led: LED,
    _objects: Sequence[TrackedPoint],
) -> RGBCCT:
    return RGBCCT()


def alternate(
    *animations: AnimationOrColor,
    length: float = 10,
) -> Animation:
    """Show each animation in turn.

    Args:
        *animations: The animations in the order to show them.
        length: The time for each animation in seconds.

    Returns:
        The animation. With no animations, all LEDs are off.
    """
    if len(animations) == 0:
        return _off

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        anim = animations[int(time / length) % len(animations)]
        return anim if isinstance(anim, RGBCCT) else anim(time, ctx, led, objects)

    return animation


def blend(
    *animations: AnimationOrColor, mode: Literal["average", "max"] = "average"
) -> Animation:
    """Mix the colors of animations channel by channel.

    Args:
        *animations: The animations to mix.
        mode: ``"average"`` uses the mean of each channel. ``"max"`` uses the
            highest value of each channel.

    Returns:
        The animation. With no animations, all LEDs are off.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        colors_list = [
            anim if isinstance(anim, RGBCCT) else anim(time, ctx, led, objects)
            for anim in animations
        ]

        if not colors_list:
            return RGBCCT()

        tuples = (
            (color.r, color.g, color.b, color.cw, color.ww) for color in colors_list
        )
        zipped = zip(*tuples, strict=True)

        if mode == "max":
            result = tuple(max(values) for values in zipped)
        else:
            result = tuple(int(sum(values) / len(colors_list)) for values in zipped)

        return RGBCCT(r=result[0], g=result[1], b=result[2], cw=result[3], ww=result[4])

    return animation


def schedule(
    primary: AnimationOrColor,
    secondary: AnimationOrColor,
    start: str = "18:00",
    end: str = "06:00",
) -> Animation:
    """Show ``primary`` between two times of the day, else ``secondary``.

    The time range can go past midnight.

    Args:
        primary: The animation inside the time range.
        secondary: The animation outside the time range.
        start: The start time as ``HH:MM``.
        end: The end time as ``HH:MM``.

    Returns:
        The animation. An invalid time gives the range 18:00 to 06:00.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        now = datetime.datetime.now().time()
        try:
            start_t = datetime.time.fromisoformat(start)
            end_t = datetime.time.fromisoformat(end)
        except ValueError:
            start_t = datetime.time(18, 0)
            end_t = datetime.time(6, 0)

        if start_t <= end_t:
            is_active = start_t <= now <= end_t
        else:
            is_active = now >= start_t or now <= end_t

        target = primary if is_active else secondary

        if isinstance(target, RGBCCT):
            return target

        return target(time, ctx, led, objects)

    return animation


def smooth(
    animation: AnimationOrColor,
    smoothing: float = 0.5,
) -> Animation:
    """Smooth an animation over time with an exponential moving average.

    Args:
        animation: The animation to smooth.
        smoothing: The weight of the previous color, from 0 to 1. 0 gives
            no smoothing. 1 keeps the first color forever.

    Returns:
        The animation.
    """
    # Keep the state as floats. Integer channels would lose small steps.
    last_colors: dict[int, _Color] = {}

    def func(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        target = (
            animation
            if isinstance(animation, RGBCCT)
            else animation(time, ctx, led, objects)
        )

        current = last_colors.get(led.index)

        if current is None:
            last_colors[led.index] = (
                float(target.r),
                float(target.g),
                float(target.b),
                float(target.cw),
                float(target.ww),
            )
            return target

        weight = 1.0 - smoothing
        next_r = current[0] * smoothing + target.r * weight
        next_g = current[1] * smoothing + target.g * weight
        next_b = current[2] * smoothing + target.b * weight
        next_cw = current[3] * smoothing + target.cw * weight
        next_ww = current[4] * smoothing + target.ww * weight

        last_colors[led.index] = (next_r, next_g, next_b, next_cw, next_ww)

        return RGBCCT(
            r=int(next_r),
            g=int(next_g),
            b=int(next_b),
            cw=int(next_cw),
            ww=int(next_ww),
        )

    return func


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


def proximity(
    primary: AnimationOrColor,
    secondary: AnimationOrColor,
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 200.0,
) -> Animation:
    """Fade between two animations from the distance of a person to a point.

    Args:
        primary: The animation when a person is at the point.
        secondary: The animation when nobody is in the radius.
        x: The x coordinate of the point.
        y: The y coordinate of the point.
        radius: The distance where ``secondary`` starts.

    Returns:
        The animation.
    """
    target_point = TrackedPoint(x=x, y=y)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        primary_color = (
            primary if isinstance(primary, RGBCCT) else primary(time, ctx, led, objects)
        )
        secondary_color = (
            secondary
            if isinstance(secondary, RGBCCT)
            else secondary(time, ctx, led, objects)
        )

        object_list = list(objects)
        if not object_list:
            return secondary_color

        min_dist = min((obj - target_point).length for obj in object_list)

        intensity = 1.0 - (min_dist / radius)
        intensity = max(intensity, 0)
        intensity = min(intensity, 1)

        return interpolate_rgbcct(
            primary_color, secondary_color, intensity, use_sign=False
        )

    return animation


# The animation time of each proximity_speed instance. The key holds the
# parameters, so two instances with the same parameters share the state.
last_time: dict[_SpeedKey, float] = {}
real_last_time: dict[_SpeedKey, float] = {}


def proximity_speed(
    animation: AnimationOrColor,
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 200.0,
    multiplier: float = 1.0,
    mode: SpeedMode = "speed up",
    proximity_factor: float = 0.5,
) -> Animation:
    """Change the speed of an animation from the distance of a person to a point.

    Args:
        animation: The animation to change.
        x: The x coordinate of the point.
        y: The y coordinate of the point.
        radius: The distance where the speed change starts.
        multiplier: The speed factor for all frames.
        mode: Make the animation faster or slower near the point.
        proximity_factor: The strength of the change, from 0 to 1.

    Returns:
        The animation.

    Raises:
        ValueError: If ``mode`` is not valid. The animation raises it on the
            first frame with a person.
    """
    target_point = TrackedPoint(x=x, y=y)

    def _animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        key = (target_point.tuple, mode, x, y, radius, multiplier)

        if last_time.get(key) is None:
            last_time[key] = time
            real_last_time[key] = time

        object_list = list(objects)
        if not object_list:
            last_time[key] += time - real_last_time[key]
            real_last_time[key] = time

            return (
                animation
                if isinstance(animation, RGBCCT)
                else animation(last_time[key], ctx, led, objects)
            )

        min_dist = min((obj - target_point).length for obj in object_list)

        intensity = (1.0 - (min_dist / radius)) * max(min(proximity_factor, 1), 0)
        intensity = max(intensity, 0)
        intensity = min(intensity, 1)

        t_diff = time - real_last_time[key]
        real_last_time[key] = time

        if mode == "speed up":
            last_time[key] = last_time[key] + t_diff / (1 - intensity) * multiplier
        elif mode == "slow down":
            last_time[key] = last_time[key] + t_diff / (1 + intensity) * multiplier
        else:
            msg = "Invalid mode"
            raise ValueError(msg)

        return (
            animation
            if isinstance(animation, RGBCCT)
            else animation(last_time[key], ctx, led, objects)
        )

    return _animation


def preset(name: str, visited_presets: set[str] | None = None) -> AnimationOrColor:
    """Load the animation of a preset file.

    Args:
        name: The name of the preset.
        visited_presets: The names of the presets that enclose this one.

    Returns:
        The animation of the preset. A missing, empty or recursive preset
        turns all LEDs off.
    """
    # gangway.config imports this module, so import it at call time.
    from ..config import ANIMATION_FUNCTIONS, CONFIG  # noqa: PLC0415

    if visited_presets is None:
        visited_presets = set()

    if name in visited_presets:
        return RGBCCT()

    new_visited = visited_presets.copy()
    new_visited.add(name)

    # The API keeps the presets next to the config file. On the Pi
    # that is the state directory, not the read-only source tree.
    preset_path = CONFIG.path.parent / "presets" / f"{name}.yaml"

    if not preset_path.exists():
        return RGBCCT()

    with open(preset_path) as f:
        anim_config: YamlValue = yaml.safe_load(f)

    if anim_config is None:
        return RGBCCT()

    return as_animation(
        parse_animation(anim_config, ANIMATION_FUNCTIONS, visited_presets=new_visited)
    )


def day_of_week(
    monday: AnimationOrColor = RGBCCT(),
    tuesday: AnimationOrColor = RGBCCT(),
    wednesday: AnimationOrColor = RGBCCT(),
    thursday: AnimationOrColor = RGBCCT(),
    friday: AnimationOrColor = RGBCCT(),
    saturday: AnimationOrColor = RGBCCT(),
    sunday: AnimationOrColor = RGBCCT(),
) -> Animation:
    """Show a different animation on each day of the week.

    Args:
        monday: The animation on Monday.
        tuesday: The animation on Tuesday.
        wednesday: The animation on Wednesday.
        thursday: The animation on Thursday.
        friday: The animation on Friday.
        saturday: The animation on Saturday.
        sunday: The animation on Sunday.

    Returns:
        The animation.
    """
    days = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        weekday = datetime.datetime.now().weekday()
        anim = days[weekday]

        if isinstance(anim, RGBCCT):
            return anim
        return anim(time, ctx, led, objects)

    return animation


def exponential_at(
    primary: AnimationOrColor = RGBCCT(r=255),
    secondary: AnimationOrColor = RGBCCT(g=255),
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 150,
) -> Animation:
    """Fade from ``secondary`` to ``primary`` near a fixed point.

    This is like `gangway.animations.responsive.exponential`, but the
    distance is to a fixed point, not to the persons.

    Args:
        primary: The animation at the point.
        secondary: The animation far from the point.
        x: The x coordinate of the point.
        y: The y coordinate of the point.
        radius: The distance that halves the weight of ``primary``.

    Returns:
        The animation.
    """
    target_point = TrackedPoint(x=x, y=y)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        intensity = 2 ** (-(led.p - target_point).length / radius)

        primary_color = (
            primary if isinstance(primary, RGBCCT) else primary(time, ctx, led, objects)
        )
        secondary_color = (
            secondary
            if isinstance(secondary, RGBCCT)
            else secondary(time, ctx, led, objects)
        )

        return interpolate_rgbcct(
            primary_color, secondary_color, intensity, use_sign=False
        )

    return animation


def strip_assignment(
    strip: int,
    animation: AnimationOrColor,
) -> tuple[int, AnimationOrColor]:
    """Assign an animation to a strip segment for `by_strip`.

    Args:
        strip: The position of the strip segment in the config.
        animation: The animation for the strip segment.

    Returns:
        The assignment.
    """
    return strip, animation


def by_strip(
    assignments: Iterable[tuple[int, AnimationOrColor]] | None = None,
    default: AnimationOrColor = RGBCCT(),
) -> Animation:
    """Show a different animation on each strip segment.

    Args:
        assignments: The animation for each strip segment, from
            `strip_assignment`.
        default: The animation for the strip segments with no assignment.

    Returns:
        The animation.
    """
    mapping = {} if assignments is None else dict(assignments)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        anim = mapping.get(led.strip_index, default)

        if isinstance(anim, RGBCCT):
            return anim
        return anim(time, ctx, led, objects)

    return animation


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
