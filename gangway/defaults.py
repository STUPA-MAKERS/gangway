"""Driver settings for the WS2805 LED chain."""

from typing import Final

LED_PIN: Final = 18
"""The GPIO pin of the data line. GPIO 18 is the PWM0 output."""

LED_FREQ_HZ: Final = 800000
"""The signal frequency in hertz."""

LED_DMA: Final = 10
"""The DMA channel of the driver."""

LED_BRIGHTNESS: Final = 255
"""The global brightness, from 0 to 255."""

LED_INVERT: Final = False
"""Set to True to invert the signal, for example with an inverting level shifter."""

LED_CHANNEL: Final = 0
"""The PWM channel of the data line."""

WS2805_STRIP: Final = 0x1F000000
"""The strip type code for WS2805 in the driver."""
