"""The render thread that drives the LED strips."""

import collections
import time
from collections.abc import Callable, Iterator, Sequence
from threading import Thread
from typing import override

from rpi_ws2805 import RGBCCT, PixelStrip

from .config import CONFIG, GANGWAYConfig
from .defaults import (
    LED_BRIGHTNESS,
    LED_CHANNEL,
    LED_DMA,
    LED_FREQ_HZ,
    LED_INVERT,
    LED_PIN,
    WS2805_STRIP,
)
from .types import (
    LED,
    SILENT_AUDIO,
    AnimationOrColor,
    AudioState,
    Rectangle,
    SceneContext,
    TrackedPoint,
)


def _silence() -> AudioState:
    return SILENT_AUDIO


class LEDController(Thread):
    """Render the active animation to the LED strips in a loop.

    Attributes:
        leds: All LEDs with their floor positions.
        running: False tells the render loop to stop after the current frame.
        strip: The LED driver.
        floor: The floor area.
        animation: The active animation.
        config: The config that the controller reads.
        current_colors: The last colors sent to the strip, by LED index.
        last_objects: The last detected persons.
        init_time: The start time of the animation, as a Unix timestamp.
        audio_source: The function that gives the latest sound snapshot.
            Its beat times use the `time.monotonic` clock.
        fps: The mean frames per second.
        tpf_min: The shortest frame time in seconds.
        tpf_max: The longest frame time in seconds.
        tpf_avg: The mean frame time in seconds.
    """

    leds: list[LED]
    running: bool = True
    strip: PixelStrip
    floor: Rectangle
    animation: AnimationOrColor

    config: GANGWAYConfig

    current_colors: dict[int, RGBCCT]
    last_objects: Sequence[TrackedPoint]

    init_time: float
    audio_source: Callable[[], AudioState]

    fps: float = 0.0
    tpf_min: float = 0.0
    tpf_max: float = 0.0
    tpf_avg: float = 0.0
    _frame_times: collections.deque[float]

    def __init__(
        self,
        gangway_config: GANGWAYConfig = CONFIG,
        audio_source: Callable[[], AudioState] = _silence,
    ) -> None:
        """Read the config and initialize the LED driver.

        Args:
            gangway_config: The config to read.
            audio_source: The function that gives the latest sound
                snapshot, for example `gangway.audio.AudioCapture.latest`.
                Its beat times must use the `time.monotonic` clock.
        """
        super().__init__()

        self.init_time = time.time()
        self.config = gangway_config
        self.audio_source = audio_source
        self.last_objects = []
        self._frame_times = collections.deque(maxlen=100)

        self.reload_config()

        self.__init_strip()

    def __init_strip(self) -> None:
        self.strip = PixelStrip(
            len(self.leds),
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            LED_BRIGHTNESS,
            LED_CHANNEL,
            strip_type=WS2805_STRIP,
        )
        self.strip.begin()

    def reload_config(self) -> None:
        """Read the LEDs, the animation and the floor from the config again."""
        self.leds = self.config.LEDS
        self.animation = self.config.ANIMATION
        self.floor = self.config.FLOOR

        if isinstance(self.animation, RGBCCT):
            self.current_colors = {led.index: self.animation for led in self.leds}
        else:
            self.current_colors = {led.index: RGBCCT(cw=255) for led in self.leds}

    @property
    def time(self) -> float:
        """The time since the start of the animation in seconds."""
        return time.time() - self.init_time

    def stop(self) -> None:
        """Stop the render loop and wait for the thread to end."""
        self.running = False
        self.join()

    def update_objects(self, objects: Sequence[TrackedPoint] = ()) -> None:
        """Set the detected persons for the next frames.

        Args:
            objects: The detected persons. An empty sequence means that
                nobody is present.
        """
        self.last_objects = objects

    def color_of(self, led: LED) -> RGBCCT:
        """Get the current color of an LED.

        Args:
            led: The LED.

        Returns:
            The color that the controller last sent to the LED.
        """
        return RGBCCT(
            value=self.current_colors[led.index] & 0xFFFFFFFFFF,
        )

    def apply_colors(self, colors: dict[int, RGBCCT]) -> None:
        """Send colors to the strip.

        Args:
            colors: The new colors, by LED index.
        """
        self.current_colors = colors

        for led in self.leds:
            self.strip.setPixelColor(led.index, self.color_of(led))

        self.strip.show()

    def frame(self) -> tuple[float, SceneContext]:
        """Get the time and the scene context for the next frame.

        Returns:
            The animation time and the scene context. All LEDs of a frame
            get the same values, so the animations can compute their frame
            values once. The context holds the latest sound snapshot, with
            the beat times moved from `time.monotonic` to the animation
            time.
        """
        # The animation time comes from the wall clock, which can jump, for
        # example on the first NTP sync of the Pi. Both clocks are read
        # together for each frame, so a beat stays at the right age after
        # a jump.
        now = self.time
        offset = now - time.monotonic()
        return now, SceneContext(
            self.floor, self.leds, self.audio_source().shifted(offset)
        )

    @property
    def context(self) -> SceneContext:
        """The scene context for the animation."""
        return self.frame()[1]

    def render(self, now: float, ctx: SceneContext) -> dict[int, RGBCCT]:
        """Get the colors of one frame.

        Args:
            now: The animation time.
            ctx: The scene context of the frame.

        Returns:
            The colors by LED index.
        """
        animation = self.animation
        objects = self.last_objects
        if isinstance(animation, RGBCCT):
            return {led.index: animation for led in self.leds}
        return {led.index: animation(now, ctx, led, objects) for led in self.leds}

    @property
    def animate(self) -> Iterator[dict[int, RGBCCT]]:
        """An endless iterator over the colors of each frame."""
        while True:
            yield self.render(*self.frame())

    @override
    def run(self) -> None:
        """Render frames until `stop` is called."""
        self.init_time = time.time()
        last_frame_start = time.perf_counter()

        for colors in self.animate:
            # The frame time includes the render time and the strip update.
            now = time.perf_counter()
            dt = now - last_frame_start
            last_frame_start = now

            if dt > 0:
                self._frame_times.append(dt)

            if len(self._frame_times) > 0:
                self.fps = 1.0 / (sum(self._frame_times) / len(self._frame_times))
                self.tpf_min = min(self._frame_times)
                self.tpf_max = max(self._frame_times)
                self.tpf_avg = sum(self._frame_times) / len(self._frame_times)

            self.apply_colors(colors)

            if not self.running:
                break
