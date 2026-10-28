"""Type stub for the rpi_ws2805 SWIG driver.

The package has no type information. This stub covers the part of the API
that gangway uses.
"""

from typing import Self

__version__: str

class RGBCCT(int):
    """Pack one color with red, green, blue, warm white and cold white channels.

    The value is an int. Each channel uses 8 bits.
    """

    def __new__(
        cls,
        r: int = 0,
        g: int = 0,
        b: int = 0,
        cw: int = 0,
        ww: int = 0,
        value: int | None = None,
    ) -> Self: ...
    @property
    def r(self) -> int:
        """Red channel."""

    @property
    def g(self) -> int:
        """Green channel."""

    @property
    def b(self) -> int:
        """Blue channel."""

    @property
    def ww(self) -> int:
        """Warm white channel."""

    @property
    def cw(self) -> int:
        """Cold white channel."""

def Color(
    red: int,
    green: int,
    blue: int,
    cold_white: int = 0,
    warm_white: int = 0,
) -> RGBCCT: ...

class PixelStrip:
    """Drive one WS2805 LED chain through the PWM or PCM peripheral."""

    size: int

    def __init__(
        self,
        num: int,
        pin: int,
        freq_hz: int = 800000,
        dma: int = 10,
        invert: bool = False,
        brightness: int = 255,
        channel: int = 0,
        strip_type: int | None = None,
        gamma: list[int] | None = None,
    ) -> None: ...
    def __len__(self) -> int: ...
    def begin(self) -> None:
        """Initialize the driver."""

    def show(self) -> None:
        """Send the LED buffer to the strip."""

    def setPixelColor(self, n: int, color: int) -> None:
        """Set the color of the LED at position n."""

    def getPixelColor(self, n: int) -> int:
        """Get the color of the LED at position n."""

    def getBrightness(self) -> int:
        """Get the global brightness."""

    def setBrightness(self, brightness: int) -> None:
        """Set the global brightness."""

    def numPixels(self) -> int:
        """Get the number of LEDs."""

class Adafruit_NeoPixel(PixelStrip):
    """Alias of PixelStrip for backward compatibility."""
