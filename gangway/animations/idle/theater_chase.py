"""The `theater_chase` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def theater_chase(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255),
    speed: float = 1.0,
    spacing: int = 4,
) -> Animation:
    """Move a pattern of lit LEDs along the LED chain.

    Args:
        color: The color of the lit LEDs.
        speed: The speed. A value of 1 gives 10 steps per second.
        spacing: The distance between two lit LEDs.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        time_offset = int(time * speed * 10)
        if (led.index - time_offset) % spacing == 0:
            return color
        return RGBCCT()

    return animation
