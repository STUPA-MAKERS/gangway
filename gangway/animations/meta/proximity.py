"""The `proximity` and `proximity_speed` animations."""

from collections.abc import Sequence
from typing import Literal

from rpi_ws2805 import RGBCCT

from ...helpers import interpolate_rgbcct
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)

type SpeedMode = Literal["speed up", "slow down"]
"""The direction of the time change of `proximity_speed`."""


type _SpeedKey = tuple[tuple[float, float], SpeedMode, float, float, float, float]


# The animation time of each proximity_speed instance. The key holds the
# parameters, so two instances with the same parameters share the state.
last_time: dict[_SpeedKey, float] = {}


real_last_time: dict[_SpeedKey, float] = {}


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
