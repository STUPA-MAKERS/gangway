"""The `static` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def static(color: RGBCCT = RGBCCT(r=255, g=255, b=255)) -> Animation:
    """Show one color on all LEDs.

    Args:
        color: The color.

    Returns:
        The animation.
    """

    def animation(
        _time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return color

    return animation
