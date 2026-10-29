"""The `spectrum` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    Axis,
    Rectangle,
    SceneContext,
    TrackedPoint,
)
from .._common import axis, channels, clamp_unit, from_channels
from ._frame import extent, mix, per_frame

_SPECTRUM_COLORS = (RGBCCT(r=255), RGBCCT(g=255), RGBCCT(b=255))


def sample(values: Sequence[float], u: float) -> float:
    """Get a value between the points of a list by linear interpolation.

    Args:
        values: The values at equal steps from 0 to 1.
        u: The position, from 0 to 1.

    Returns:
        The interpolated value. An empty list gives 0, and a list with one
        value gives that value.
    """
    if len(values) < 2:
        return values[0] if values else 0.0
    x = clamp_unit(u) * (len(values) - 1)
    i = min(int(x), len(values) - 2)
    return values[i] + (values[i + 1] - values[i]) * (x - i)


def gradient(colors: Sequence[RGBCCT], u: float) -> RGBCCT:
    """Get a color between the colors of a palette.

    Args:
        colors: The colors at equal steps from 0 to 1.
        u: The position, from 0 to 1.

    Returns:
        The interpolated color. An empty palette gives black.
    """
    if not colors:
        return RGBCCT()
    per_channel = zip(*map(channels, colors), strict=True)
    return from_channels(sample(values, u) for values in per_channel)


def spectrum(
    colors: Sequence[RGBCCT] = _SPECTRUM_COLORS,
    background: AnimationOrColor = RGBCCT(),
    direction: Axis = Axis.Y,
    reverse: bool = False,
    min_brightness: float = 0.0,
) -> Animation:
    """Show the floor as an equalizer: the bass at one end, the treble at the other.

    Each LED gets the energy of the frequency band at its position on the
    axis. The energy sets the brightness of the palette color at that
    position.

    Args:
        colors: The palette from the bass end to the treble end.
        background: The animation where the energy is low.
        direction: The axis from bass to treble.
        reverse: Set to True to put the bass at the high end of the axis.
        min_brightness: The lowest brightness of the palette color, from 0
            to 1. A value above 0 keeps the palette visible in silence.

    Returns:
        The animation. It reads the narrow bands of `AudioState.spectrum`,
        or bass, mid and treble if the snapshot has no spectrum. It keeps
        the position and the palette color of each LED until the floor
        changes.
    """
    coord = axis(direction)
    floor_weight = clamp_unit(min_brightness)
    # The position and the palette color of an LED change only with the
    # floor, so the animation keeps them for each LED.
    layout: dict[int, tuple[float, RGBCCT]] = {}
    layout_floor: list[Rectangle] = []

    def bands(_time: float, ctx: SceneContext) -> tuple[float, ...]:
        if not layout_floor or layout_floor[0] is not ctx.floor:
            layout.clear()
            layout_floor[:] = [ctx.floor]
        audio = ctx.audio
        return audio.spectrum or (audio.bass, audio.mid, audio.treble)

    frame_bands = per_frame(bands)

    def place(ctx: SceneContext, led: LED) -> tuple[float, RGBCCT]:
        lo, hi = extent(ctx.floor, direction)
        u = clamp_unit((coord(led.p) - lo) / (hi - lo)) if hi > lo else 0.0
        u = 1 - u if reverse else u
        return u, gradient(colors, u)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        values = frame_bands(time, ctx)
        placed = layout.get(led.index)
        if placed is None:
            placed = layout[led.index] = place(ctx, led)
        u, color = placed
        base = render(background, time, ctx, led, objects)
        return mix(color, base, floor_weight + (1 - floor_weight) * sample(values, u))

    return animation
