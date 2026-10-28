"""The `lightning_storm` animation."""

import math
import random
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint


def lightning_storm(
    frequency: float = 0.02,
    base_brightness: float = 0.00,
) -> Animation:
    """Show random bright flashes over a dim background, like lightning.

    Args:
        frequency: The probability of a flash in each 0.5 second period.
        base_brightness: The cold white background level, from 0 to 1.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        flash_period = 0.5
        flash_time = time % flash_period
        flash_seed = int(time / flash_period)

        rng = random.Random(flash_seed)
        has_flash = rng.random() < frequency

        if has_flash and flash_time < 0.2:
            # A seed from the LED index gives each LED a different flicker.
            led_flicker = random.Random(flash_seed + led.index).random() * 0.4 + 0.6
            flash_intensity = (
                math.exp(-flash_time * 15)
                * led_flicker
                * (math.sin(time * 100) * 0.2 + 0.8)
            )
            val = int(255 * flash_intensity)
            return RGBCCT(r=val, g=val, b=val, cw=val, ww=val)

        base = int(255 * base_brightness)
        return RGBCCT(cw=base)

    return animation
