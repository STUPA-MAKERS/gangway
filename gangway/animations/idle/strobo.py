"""The `strobo` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint

_STROBO_COLORS = (
    RGBCCT(r=255, g=255, b=255, cw=255, ww=255),
    RGBCCT(),
    RGBCCT(r=255),
    RGBCCT(),
    RGBCCT(b=255),
)


def strobo(
    colors: Sequence[RGBCCT] = _STROBO_COLORS,
    frequency: int = 100,
) -> Animation:
    """Show a sequence of colors on all LEDs, one color for each step.

    Args:
        colors: The color sequence.
        frequency: The number of steps per second.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return colors[int(time * frequency) % len(colors)]

    return animation
