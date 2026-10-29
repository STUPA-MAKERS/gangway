"""API endpoints for live data: persons, LED colors, frame rates and sound."""

import math
import time
from typing import TypedDict

from fastapi import APIRouter

from ..state import STATE
from ..types import SILENT_AUDIO

router = APIRouter()


class ColorData(TypedDict):
    """The channels of one LED color.

    Attributes:
        r: Red channel.
        g: Green channel.
        b: Blue channel.
        cw: Cold white channel.
        ww: Warm white channel.
    """

    r: int
    g: int
    b: int
    cw: int
    ww: int


class FpsData(TypedDict):
    """The render and sensor rates.

    Attributes:
        fps: The mean frames per second.
        tpf_min: The shortest frame time in milliseconds.
        tpf_max: The longest frame time in milliseconds.
        tpf_avg: The mean frame time in milliseconds.
        ups: The sensor requests in the last second.
    """

    fps: int | float
    tpf_min: int | float
    tpf_max: int | float
    tpf_avg: int | float
    ups: int | float


class AudioData(TypedDict):
    """The sound analysis.

    Attributes:
        capturing: True while the microphone gives samples.
        level: The loudness, from 0 to 1.
        bass: The bass energy, from 0 to 1.
        mid: The mid energy, from 0 to 1.
        treble: The treble energy, from 0 to 1.
        spectrum: The energy of the narrow bands, from low to high.
        beat_count: The number of beats since the start.
        since_beat: The time since the last beat in seconds, or None.
        tempo: The tempo in beats per minute, or 0 if not known.
    """

    capturing: bool
    level: float
    bass: float
    mid: float
    treble: float
    spectrum: list[float]
    beat_count: int
    since_beat: float | None
    tempo: float


@router.get("/objects")
def get_objects() -> list[dict[str, float]]:
    """Get the floor positions of the detected persons.

    Returns:
        The positions as ``{"x": ..., "y": ...}`` items. The list is empty
        before the LED controller starts.
    """
    if not STATE.led_controller:
        return []

    return [{"x": p.x, "y": p.y} for p in STATE.objects]


@router.get("/leds")
def get_leds() -> dict[int, ColorData]:
    """Get the current color of each LED.

    Returns:
        The colors by LED index. The mapping is empty before the LED
        controller starts.
    """
    if not STATE.led_controller:
        return {}

    leds_data: dict[int, ColorData] = {}
    for led in STATE.led_controller.leds:
        color = STATE.led_controller.color_of(led)
        leds_data[led.index] = {
            "r": color.r,
            "g": color.g,
            "b": color.b,
            "cw": color.cw,
            "ww": color.ww,
        }
    return leds_data


@router.get("/fps")
def get_fps() -> FpsData:
    """Get the render and sensor rates.

    Returns:
        The rates. All values are 0 before the LED controller starts.
    """
    if not STATE.led_controller:
        return {"fps": 0, "tpf_min": 0, "tpf_max": 0, "tpf_avg": 0, "ups": 0}

    ups = 0
    if STATE.xovis_server:
        ups = STATE.xovis_server.ups

    return {
        "fps": round(STATE.led_controller.fps, 2),
        "tpf_min": round(STATE.led_controller.tpf_min * 1000, 2),
        "tpf_max": round(STATE.led_controller.tpf_max * 1000, 2),
        "tpf_avg": round(STATE.led_controller.tpf_avg * 1000, 2),
        "ups": round(ups, 2),
    }


@router.get("/audio")
def get_audio() -> AudioData:
    """Get the latest sound analysis, to tune the microphone settings.

    Returns:
        The values of the latest snapshot. All values are 0 if the audio is
        off or if the microphone is missing.
    """
    capture = STATE.audio_capture
    audio = capture.latest() if capture else SILENT_AUDIO
    # The beat times of the capture thread use the monotonic clock.
    since_beat = time.monotonic() - audio.last_beat
    return {
        "capturing": bool(capture and capture.capturing),
        "level": round(audio.level, 3),
        "bass": round(audio.bass, 3),
        "mid": round(audio.mid, 3),
        "treble": round(audio.treble, 3),
        "spectrum": [round(v, 3) for v in audio.spectrum],
        "beat_count": audio.beat_count,
        "since_beat": round(since_beat, 3) if math.isfinite(since_beat) else None,
        "tempo": round(audio.tempo, 1),
    }
