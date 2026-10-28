"""The `off` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def off() -> Animation:
    """Turn all LEDs off.

    Returns:
        The animation.
    """

    def animation(
        _time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return RGBCCT()

    return animation
