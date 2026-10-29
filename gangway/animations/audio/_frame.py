"""Helpers that the audio animations share."""

from collections.abc import Callable

from rpi_ws2805 import RGBCCT

from ...types import AudioState, Axis, Rectangle, SceneContext


def per_frame[T](
    compute: Callable[[float, SceneContext], T],
) -> Callable[[float, SceneContext], T]:
    """Cache a frame value for all LEDs of the frame.

    The animation gets one call for each LED. A value that depends only on
    the time and the context is the same for all of them, so it is
    computed on the first call of a frame.

    Args:
        compute: The function that computes the frame value.

    Returns:
        The function with the cache. A different time, sound snapshot or
        floor object starts a new frame.
    """
    cache: tuple[float, AudioState, Rectangle, T] | None = None

    def cached(time: float, ctx: SceneContext) -> T:
        nonlocal cache
        if (
            cache is None
            or cache[0] != time
            or cache[1] is not ctx.audio
            or cache[2] is not ctx.floor
        ):
            cache = (time, ctx.audio, ctx.floor, compute(time, ctx))
        return cache[3]

    return cached


def extent(floor: Rectangle, direction: Axis) -> tuple[float, float]:
    """Get the range of the floor along an axis.

    Args:
        floor: The floor area.
        direction: The axis. A value other than `Axis.X` selects the y axis.

    Returns:
        The lowest and the highest coordinate.
    """
    a, b = (floor.p1.x, floor.p2.x) if direction == Axis.X else (floor.p1.y, floor.p2.y)
    return min(a, b), max(a, b)


_SHIFTS = (0, 8, 16, 24, 32)
"""The bit positions of the channels in the integer value of `RGBCCT`."""


def mix(color: RGBCCT, background: RGBCCT, weight: float) -> RGBCCT:
    """Mix a color over a background.

    Args:
        color: The color.
        background: The background.
        weight: The weight of ``color``, from 0 to 1.

    Returns:
        The mixed color, with each channel truncated to an integer. A
        weight of 0 or 1 gives one of the input objects, which saves the
        channel math on most LEDs.
    """
    if weight <= 0:
        return background
    if weight >= 1:
        return color
    # The audio animations call this for each LED in each frame. The bit
    # operations on the packed value are faster than the channel properties
    # of RGBCCT.
    c, b = int(color), int(background)
    value = 0
    for shift in _SHIFTS:
        low = (b >> shift) & 0xFF
        value |= int(low + (((c >> shift) & 0xFF) - low) * weight) << shift
    return RGBCCT(value=value)


def gain(color: RGBCCT, factor: float) -> RGBCCT:
    """Multiply all channels of a color by a factor, limited to 255.

    Args:
        color: The color.
        factor: The factor, 0 or more.

    Returns:
        The scaled color, with each channel truncated to an integer.
    """
    c = int(color)
    value = 0
    for shift in _SHIFTS:
        value |= min(int(((c >> shift) & 0xFF) * factor), 255) << shift
    return RGBCCT(value=value)
