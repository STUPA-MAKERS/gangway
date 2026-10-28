"""API endpoints for live data: persons, LED colors and frame rates."""

from typing import TypedDict

from fastapi import APIRouter

from ..state import STATE

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
