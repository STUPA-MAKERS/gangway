"""The `rave` animation."""

from rpi_ws2805 import RGBCCT

from ...types import Animation
from ..meta import alternate, blend
from .rainbow import rainbow
from .sparkle import sparkle
from .strobo import strobo
from .theater_chase import theater_chase


def rave() -> Animation:
    """Alternate between strobe, glitter rainbow, chase and sparkle effects.

    Returns:
        The animation.
    """
    strobe_anim = strobo(
        colors=[
            RGBCCT(r=255),
            RGBCCT(),
            RGBCCT(g=255),
            RGBCCT(),
            RGBCCT(b=255),
            RGBCCT(),
            RGBCCT(cw=255),
            RGBCCT(),
        ],
        frequency=75,
    )
    rainbow_anim = rainbow(speed=2.0, spread=2.0)
    sparkle_anim = sparkle(density=0.2, speed=30.0)
    chase_anim = theater_chase(color=RGBCCT(r=255, g=0, b=255), speed=4.0, spacing=5)

    return alternate(
        strobe_anim,
        blend(rainbow_anim, sparkle_anim),
        chase_anim,
        sparkle_anim,
        length=1.5,
    )
