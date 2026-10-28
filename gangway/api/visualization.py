"""API endpoints that draw the floor, the strips and the camera view."""

import cv2
import numpy as np
import requests
from fastapi import APIRouter
from fastapi.responses import Response

from .. import config
from ..helpers import to_hex
from ..led_controller import LEDController
from ..state import STATE
from ..xovis.homographic_projection import get_homography

router = APIRouter()

_LIVE_URL = "http://localhost:80/live"
"""The camera image of the Xovis sensor, through the local reverse proxy."""


def _svg(controller: LEDController, body: str, defs: str = "") -> str:
    floor = controller.floor
    head = (
        f'<svg width="{floor.p2.x}" height="{floor.p2.y}" '
        'xmlns="http://www.w3.org/2000/svg">'
    )
    if defs:
        head += f"<defs>{defs}</defs>"
    return (
        f'{head}<rect width="100%" height="100%" fill="transparent" stroke="black"/>'
        f"{body}</svg>"
    )


def _line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: int) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{stroke}" stroke-width="{width}" />'
    )


@router.get("/objects", response_class=Response)
def get_objects() -> Response:
    """Draw the detected persons as an SVG image.

    Returns:
        The SVG image, or 503 before the LED controller starts.
    """
    controller = STATE.led_controller
    if not controller:
        return Response(status_code=503, content="LED Controller not ready")

    svg_elements = [
        f'<circle cx="{p.x}" cy="{p.y}" r="5" fill="red" />' for p in STATE.objects
    ]

    content = _svg(controller, "".join(svg_elements))
    return Response(content=content, media_type="image/svg+xml")


@router.get("/strips", response_class=Response)
def get_strips() -> Response:
    """Draw the LED strip segments as an SVG image.

    Returns:
        The SVG image, or 503 before the LED controller starts.
    """
    controller = STATE.led_controller
    if not controller:
        return Response(status_code=503, content="LED Controller not ready")

    svg_elements = [
        _line(s.start.x, s.start.y, s.end.x, s.end.y, "black", 5)
        for s in config.CONFIG.STRIPS
    ]

    content = _svg(controller, "".join(svg_elements))
    return Response(content=content, media_type="image/svg+xml")


@router.get("/state", response_class=Response)
def get_state() -> Response:
    """Draw the strip segments with their current LED colors as an SVG image.

    Returns:
        The SVG image, or 503 before the LED controller starts.
    """
    controller = STATE.led_controller
    if not controller:
        return Response(status_code=503, content="LED Controller not ready")

    defs: list[str] = []
    svg_elements: list[str] = []

    for i, strip in enumerate(config.CONFIG.STRIPS):
        gradient_id = f"gradient{i}"
        stops: list[str] = []
        for j in range(strip.len):
            led_index = strip.index + j
            led = next(
                (led for led in controller.leds if led.index == led_index),
                None,
            )
            if led:
                hex_color = to_hex(controller.color_of(led))
                offset = j / (strip.len - 1)
                stops.append(f'<stop offset="{offset}" stop-color="{hex_color}" />')
        defs.append(
            f'<linearGradient id="{gradient_id}" x1="{strip.start.x}" '
            f'y1="{strip.start.y}" x2="{strip.end.x}" y2="{strip.end.y}" '
            f'gradientUnits="userSpaceOnUse">{"".join(stops)}</linearGradient>'
        )
        coords = (strip.start.x, strip.start.y, strip.end.x, strip.end.y)
        svg_elements.append(_line(*coords, "black", 7))
        svg_elements.append(_line(*coords, f"url(#{gradient_id})", 5))

    content = _svg(controller, "".join(svg_elements), defs="".join(defs))
    return Response(content=content, media_type="image/svg+xml")


@router.get("/live", response_class=Response)
def get_live() -> Response:
    """Get the camera image of the sensor, rotated by 180 degrees.

    Returns:
        The JPEG image, or an error response.
    """
    try:
        response = requests.get(_LIVE_URL, verify=False)
        response.raise_for_status()

        image_array = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if img is None:
            return Response(status_code=502, content="Failed to decode upstream image")

        img = cv2.flip(img, -1)

        is_success, buffer = cv2.imencode(".jpg", img)
        if not is_success:
            return Response(status_code=500, content="Failed to encode image")

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    except Exception as e:
        print(f"Error in /live: {e}")
        return Response(status_code=500, content=str(e))


@router.get("/homography")
def get_homography_data() -> dict[str, list[list[float]]]:
    """Get the matrix that maps the camera cutout to the floor.

    Returns:
        The 3x3 matrix as nested lists.
    """
    matrix = get_homography(src=config.CONFIG.CUTOUT)
    rows: list[list[float]] = matrix.tolist()
    return {"matrix": rows}


@router.get("/live_mapped", response_class=Response)
def get_live_mapped() -> Response:
    """Get the camera image of the sensor, projected to the floor plan.

    Returns:
        The JPEG image, or an error response.
    """
    controller = STATE.led_controller
    if not controller:
        return Response(status_code=503, content="LED Controller not ready")

    try:
        response = requests.get(_LIVE_URL, verify=False)
        response.raise_for_status()

        image_array = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if img is None:
            return Response(status_code=502, content="Failed to decode upstream image")

        matrix = get_homography(src=config.CONFIG.CUTOUT)

        width = int(controller.floor.p2.x)
        height = int(controller.floor.p2.y)

        img = cv2.flip(img, -1)
        warped_img = cv2.warpPerspective(img, matrix, (width, height))
        warped_img = cv2.flip(warped_img, 0)

        is_success, buffer = cv2.imencode(".jpg", warped_img)
        if not is_success:
            return Response(status_code=500, content="Failed to encode image")

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    except Exception as e:
        print(f"Error in /live: {e}")
        return Response(status_code=500, content=str(e))
