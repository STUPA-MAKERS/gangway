"""Pure helpers that the animations of all packages share."""

from collections.abc import Callable, Iterable, Sequence

from rpi_ws2805 import RGBCCT

from ..helpers import render
from ..types import LED, AnimationOrColor, Axis, Point, SceneContext, TrackedPoint

type Channels = tuple[int, int, int, int, int]
"""The ``r``, ``g``, ``b``, ``cw`` and ``ww`` channels of a color."""


def _x(p: Point) -> float:
    return p.x


def _y(p: Point) -> float:
    return p.y


def axis(direction: Axis) -> Callable[[Point], float]:
    """Get a function that reads one coordinate of a point.

    Args:
        direction: The axis. A value other than `Axis.X` selects the y axis.

    Returns:
        The function that returns the coordinate on that axis.
    """
    match direction:
        case Axis.X:
            return _x
        case _:
            return _y


def channels(color: RGBCCT) -> Channels:
    """Get the channels of a color.

    Args:
        color: The color.

    Returns:
        The channels in the argument order of `RGBCCT`.
    """
    return (color.r, color.g, color.b, color.cw, color.ww)


def from_channels(values: Iterable[float]) -> RGBCCT:
    """Make a color from channel values.

    Args:
        values: The ``r``, ``g``, ``b``, ``cw`` and ``ww`` values. The
            function truncates each value to an integer.

    Returns:
        The color.
    """
    return RGBCCT(*map(int, values))


def scale(color: RGBCCT, factor: float) -> RGBCCT:
    """Multiply all channels of a color by a factor.

    Args:
        color: The color.
        factor: The factor.

    Returns:
        The scaled color, with each channel truncated to an integer.
    """
    return from_channels(value * factor for value in channels(color))


def clamp_unit(value: float) -> float:
    """Limit a value to the range from 0 to 1.

    Args:
        value: The value.

    Returns:
        The limited value.
    """
    return min(max(value, 0), 1)


def render_pair(
    primary: AnimationOrColor,
    secondary: AnimationOrColor,
    time: float,
    ctx: SceneContext,
    led: LED,
    objects: Sequence[TrackedPoint],
) -> tuple[RGBCCT, RGBCCT]:
    """Get the colors of two animations for the same LED and frame.

    The function always renders both animations, in this order. A stateful
    or a random sub-animation thus sees the same calls in each frame.

    Args:
        primary: The first animation.
        secondary: The second animation.
        time: The animation time in seconds.
        ctx: The scene context.
        led: The LED.
        objects: The detected persons.

    Returns:
        The color of ``primary`` and the color of ``secondary``.
    """
    return (
        render(primary, time, ctx, led, objects),
        render(secondary, time, ctx, led, objects),
    )


def dark(
    _time: float,
    _ctx: SceneContext,
    _led: LED,
    _objects: Sequence[TrackedPoint],
) -> RGBCCT:
    """Turn the LED off.

    Args:
        _time: Not used.
        _ctx: Not used.
        _led: Not used.
        _objects: Not used.

    Returns:
        The color with all channels at 0.
    """
    return RGBCCT()
