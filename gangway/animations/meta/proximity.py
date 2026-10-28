"""The `proximity` and `proximity_speed` animations."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import interpolate_rgbcct, render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    SpeedMode,
    TrackedPoint,
)
from .._common import clamp_unit, render_pair


def _closest(target: TrackedPoint, objects: Sequence[TrackedPoint]) -> float:
    """Get the distance from ``target`` to the closest person."""
    return min((obj - target).length for obj in objects)


def _advance(
    animation_time: float,
    t_diff: float,
    intensity: float,
    multiplier: float,
    mode: str,
) -> float:
    """Get the animation time of the next frame.

    The config can give any string, so the function checks the mode at run
    time.

    Raises:
        ValueError: If ``mode`` is not valid.
    """
    match mode:
        case SpeedMode.SPEED_UP:
            return animation_time + t_diff / (1 - intensity) * multiplier
        case SpeedMode.SLOW_DOWN:
            return animation_time + t_diff / (1 + intensity) * multiplier
        case _:
            msg = "Invalid mode"
            raise ValueError(msg)


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
        near, far = render_pair(primary, secondary, time, ctx, led, objects)
        if not objects:
            return far
        intensity = clamp_unit(1.0 - (_closest(target_point, objects) / radius))
        return interpolate_rgbcct(near, far, intensity, use_sign=False)

    return animation


def proximity_speed(
    animation: AnimationOrColor,
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 200.0,
    multiplier: float = 1.0,
    mode: SpeedMode = SpeedMode.SPEED_UP,
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
        The animation. The animation time is the sum of the scaled time
        steps of all earlier frames, so the animation keeps the pair of
        animation time and real time. The real time also moves on when a
        frame raises an error.

    Raises:
        ValueError: If ``mode`` is not valid. The animation raises it on the
            first frame with a person.
    """
    target_point = TrackedPoint(x=x, y=y)
    factor = max(min(proximity_factor, 1), 0)
    clock: tuple[float, float] | None = None

    def _animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        nonlocal clock
        animation_time, real_time = clock or (time, time)
        clock = (animation_time, time)
        next_time = (
            _advance(
                animation_time,
                time - real_time,
                clamp_unit((1.0 - (_closest(target_point, objects) / radius)) * factor),
                multiplier,
                mode,
            )
            if objects
            else animation_time + (time - real_time)
        )
        clock = (next_time, time)
        return render(animation, next_time, ctx, led, objects)

    return _animation
