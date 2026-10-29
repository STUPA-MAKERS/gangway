"""Tests for the audio animations with hand-made sound snapshots."""

import math
import time
from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest
from rpi_ws2805 import RGBCCT

from gangway import led_controller
from gangway.animations.audio import (
    audio_gain,
    beat_pulse,
    beat_ripples,
    beat_switch,
    beat_wave,
    level,
    spectrum,
)
from gangway.config import ANIMATION_FUNCTIONS
from gangway.helpers import as_animation, parse_animation
from gangway.types import (
    LED,
    AudioSource,
    AudioState,
    Axis,
    Point,
    Rectangle,
    SceneContext,
    TrackedPoint,
)

WHITE = RGBCCT(r=255, g=255, b=255)
RED = RGBCCT(r=255)
GREEN = RGBCCT(g=255)
BLUE = RGBCCT(b=255)
BLACK = RGBCCT()
FLOOR = Rectangle(Point(0, 0), Point(100, 400))


def _ctx(audio: AudioState) -> SceneContext:
    return SceneContext(floor=FLOOR, leds=[], audio=audio)


def _led(y: float, x: float = 50) -> LED:
    return LED(index=int(y), p=Point(x, y))


def test_beat_wave_front_moves_along_the_axis() -> None:
    """A front starts at the low end and moves at the given speed."""
    anim = beat_wave(RED, BLACK, direction=Axis.Y, speed=100, width=20)
    ctx = _ctx(AudioState(beats=(0.0,)))
    # At t = 1 the front is at y = 100 and its tail reaches back to y = 80.
    assert anim(1.0, ctx, _led(100), []) == RED
    assert anim(1.0, ctx, _led(95), []) == RGBCCT(r=191)
    assert anim(1.0, ctx, _led(105), []) == BLACK
    assert anim(1.0, ctx, _led(50), []) == BLACK
    assert anim(2.0, ctx, _led(200), []) == RED
    assert anim(2.0, ctx, _led(100), []) == BLACK


def test_beat_wave_reverse_and_many_fronts() -> None:
    """Reverse starts at the high end, and each beat adds a front."""
    anim = beat_wave(RED, BLACK, direction=Axis.Y, reverse=True, speed=100, width=20)
    ctx = _ctx(AudioState(beats=(0.0, 1.0)))
    assert anim(2.0, ctx, _led(200), []) == RED
    assert anim(2.0, ctx, _led(300), []) == RED
    assert anim(2.0, ctx, _led(250), []) == BLACK


def test_beat_wave_front_ends_after_the_floor() -> None:
    """A front is gone after its tail leaves the floor."""
    anim = beat_wave(RED, GREEN, direction=Axis.Y, speed=100, width=20)
    ctx = _ctx(AudioState(beats=(0.0,)))
    assert anim(4.05, ctx, _led(399), []) == RGBCCT(r=178, g=76)
    assert anim(5.0, ctx, _led(399), []) == GREEN


def test_beat_ripples_ring_around_a_person() -> None:
    """A ring grows from each person and fades with the radius."""
    anim = beat_ripples(WHITE, BLACK, speed=100, width=10, max_radius=200)
    ctx = _ctx(AudioState(beats=(0.0,)))
    person = [TrackedPoint(50, 200)]
    assert anim(1.0, ctx, _led(300), person) == RGBCCT(r=127, g=127, b=127)
    assert anim(1.0, ctx, _led(200), person) == BLACK
    assert anim(1.0, ctx, _led(300), []) == BLACK
    assert anim(3.0, ctx, _led(300), person) == BLACK


def test_beat_pulse_decays_exponentially() -> None:
    """The flash starts at full strength and fades with the time constant."""
    anim = beat_pulse(WHITE, BLACK, decay=0.5)
    ctx = _ctx(AudioState(last_beat=10.0))
    assert anim(10.0, ctx, _led(0), []) == WHITE
    assert anim(10.5, ctx, _led(0), []) == RGBCCT(r=93, g=93, b=93)
    assert anim(20.0, ctx, _led(0), []) == BLACK
    assert anim(0.0, _ctx(AudioState()), _led(0), []) == BLACK


def test_level_fills_the_bar_and_holds_the_peak() -> None:
    """The bar follows the level, and the peak dot falls slowly."""
    anim = level(GREEN, RED, BLACK, direction=Axis.Y, peak_fall=0.1, peak_width=10)
    loud = _ctx(AudioState(level=0.5))
    assert anim(0.0, loud, _led(100), []) == GREEN
    assert anim(0.0, loud, _led(200), []) == RED
    assert anim(0.0, loud, _led(300), []) == BLACK

    quiet = _ctx(AudioState(level=0.0))
    assert anim(1.0, quiet, _led(100), []) == BLACK
    # The peak falls by 0.1 of the floor length in one second.
    assert anim(1.0, quiet, _led(160), []) == RED


def test_level_reads_the_source() -> None:
    """The source selects the audio value of the bar."""
    anim = level(GREEN, RED, BLACK, source=AudioSource.BASS, peak_width=0)
    ctx = _ctx(AudioState(level=0.0, bass=1.0))
    assert anim(0.0, ctx, _led(390), []) == GREEN


def test_spectrum_puts_bass_and_treble_at_the_ends() -> None:
    """The bass band lights the low end, the treble band the high end."""
    anim = spectrum([RED, BLUE], BLACK, direction=Axis.Y)
    bass = _ctx(AudioState(spectrum=(1.0, 0.0, 0.0, 0.0)))
    assert anim(0.0, bass, _led(0), []) == RED
    assert anim(0.0, bass, _led(400), []) == BLACK

    treble = _ctx(AudioState(bass=0.0, mid=0.0, treble=1.0))
    assert anim(0.0, treble, _led(400), []) == BLUE
    assert anim(0.0, treble, _led(0), []) == BLACK


def test_spectrum_reverse_and_min_brightness() -> None:
    """Reverse puts the bass at the high end, and silence shows the floor."""
    anim = spectrum([RED, BLUE], BLACK, reverse=True, min_brightness=0.2)
    ctx = _ctx(AudioState(bass=1.0))
    assert anim(0.0, ctx, _led(400), []) == RED
    assert anim(0.0, ctx, _led(0), []) == RGBCCT(b=51)


def test_beat_switch_steps_after_the_beats() -> None:
    """Each animation shows for the given number of beats, then the next."""
    anim = beat_switch(RED, GREEN, BLUE, beats_per_switch=2)
    colors = [anim(0.0, _ctx(AudioState(beat_count=n)), _led(0), []) for n in range(7)]
    assert colors == [RED, RED, GREEN, GREEN, BLUE, BLUE, RED]
    assert beat_switch()(0.0, _ctx(AudioState()), _led(0), []) == BLACK


@pytest.mark.parametrize(
    ("value", "min_gain", "max_gain", "expected"),
    [
        (0.5, 0.0, 1.0, RGBCCT(r=100)),
        (0.0, 0.25, 1.0, RGBCCT(r=50)),
        (1.0, 0.0, 2.0, RGBCCT(r=255)),
    ],
)
def test_audio_gain_scales_the_brightness(
    value: float, min_gain: float, max_gain: float, expected: RGBCCT
) -> None:
    """The gain goes from min_gain in silence to max_gain at the peak."""
    anim = audio_gain(RGBCCT(r=200), AudioSource.MID, min_gain, max_gain)
    assert anim(0.0, _ctx(AudioState(mid=value)), _led(0), []) == expected


def test_audio_animations_are_in_the_registry() -> None:
    """The config can build the audio animations by name."""
    anim = as_animation(
        parse_animation(
            {
                "beat_switch": {
                    "animations": [
                        {"beat_pulse": {"decay": 0.1}},
                        {"audio_gain": {"animation": {"r": 9, "g": 0, "b": 0}}},
                    ],
                    "beats_per_switch": 1,
                }
            },
            ANIMATION_FUNCTIONS,
        )
    )
    assert not isinstance(anim, RGBCCT)
    ctx = _ctx(AudioState(level=1.0, beat_count=1))
    assert anim(0.0, ctx, _led(0), []) == RGBCCT(r=9)


def test_controller_moves_beats_to_the_animation_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The controller gives one time per frame and beats on that clock."""
    monkeypatch.setattr(led_controller, "PixelStrip", MagicMock())
    beat = time.monotonic() - 0.5
    controller = led_controller.LEDController(
        audio_source=lambda: AudioState(last_beat=beat, beats=(beat,))
    )
    seen: list[float] = []

    def record(
        t: float, ctx: SceneContext, _led: LED, _objects: Sequence[TrackedPoint]
    ) -> RGBCCT:
        seen.append(t - ctx.audio.last_beat)
        return BLACK

    controller.animation = record
    now, ctx = controller.frame()
    assert math.isclose(now - ctx.audio.last_beat, 0.5, abs_tol=0.05)
    assert ctx.audio.beats == (ctx.audio.last_beat,)

    _ = controller.render(now, ctx)
    assert len(seen) == len(controller.leds)
    assert len(set(seen)) == 1
