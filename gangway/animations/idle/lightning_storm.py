"""The `lightning_storm` animation."""

import math
import random
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, SceneContext, TrackedPoint

_FLASH_PERIOD = 0.5
_FLASH_LENGTH = 0.2


def _flash(time: float, flash_time: float, flash_seed: int, led: LED) -> RGBCCT:
    """Get the color of one LED during a flash.

    A seed from the LED index gives each LED a different flicker.
    """
    led_flicker = random.Random(flash_seed + led.index).random() * 0.4 + 0.6
    intensity = (
        math.exp(-flash_time * 15) * led_flicker * (math.sin(time * 100) * 0.2 + 0.8)
    )
    val = int(255 * intensity)
    return RGBCCT(r=val, g=val, b=val, cw=val, ww=val)


def lightning_storm(
    frequency: float = 0.02,
    base_brightness: float = 0.00,
) -> Animation:
    """Show random bright flashes over a dim background, like lightning.

    All LEDs use the same seed for the flash decision, so they flash
    together.

    Args:
        frequency: The probability of a flash in each 0.5 second period.
        base_brightness: The cold white background level, from 0 to 1.

    Returns:
        The animation.
    """
    background = RGBCCT(cw=int(255 * base_brightness))

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        flash_time = time % _FLASH_PERIOD
        flash_seed = int(time / _FLASH_PERIOD)
        has_flash = random.Random(flash_seed).random() < frequency
        return (
            _flash(time, flash_time, flash_seed, led)
            if has_flash and flash_time < _FLASH_LENGTH
            else background
        )

    return animation
