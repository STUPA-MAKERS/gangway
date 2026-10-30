"""API endpoints for the statistics of the sensor: counts, health and heat map."""

import os
from datetime import datetime, timedelta
from typing import Final, Literal, TypedDict
from zoneinfo import ZoneInfo

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..xovis.sensor_api import (
    SENSOR,
    Count,
    SensorClient,
    SensorError,
    bucket,
    hours_before,
    start_of_day,
    start_of_hour,
    start_of_week,
    total,
)

router = APIRouter()

TIMEZONE: Final = ZoneInfo(os.getenv("GANGWAY_TIMEZONE", "Europe/Berlin"))
"""The timezone of the days and the weeks of the statistics."""

type Range = Literal["day", "week", "month"]


class Bucket(TypedDict):
    """The persons in one time bucket.

    Attributes:
        start: The start of the bucket, as ISO 8601 with offset.
        entered: The persons that went in.
        left: The persons that went out.
    """

    start: str
    entered: int
    left: int


class Counts(TypedDict):
    """A time series of the persons.

    Attributes:
        granularity: The length of one bucket.
        buckets: The buckets, oldest first.
        entered: The persons that went in, in all buckets.
        left: The persons that went out, in all buckets.
    """

    granularity: Literal["hour", "day"]
    buckets: list[Bucket]
    entered: int
    left: int


class Total(TypedDict):
    """The persons in a time range.

    Attributes:
        entered: The persons that went in.
        left: The persons that went out.
    """

    entered: int
    left: int


class Summary(TypedDict):
    """The totals for the overview.

    Attributes:
        today: Since midnight.
        yesterday: The day before today.
        week: Since Monday midnight.
        last_30_days: The last 30 days, today included.
        busiest_hour: The start of the hour of today with the most crossings,
            or None if nobody crossed today.
    """

    today: Total
    yesterday: Total
    week: Total
    last_30_days: Total
    busiest_hour: str | None


class Health(TypedDict):
    """The health of the sensor. See `SensorStatus`.

    Attributes:
        name: The name of the sensor.
        software: The software version.
        device: The device type.
        uptime: The time since the last start of the sensor, in seconds.
        temperature_die: The temperature of the chip in °C, or None.
        temperature_housing: The temperature of the housing in °C, or None.
        illumination_ok: Whether the scene has enough light to count.
        mode: The operation mode, for example ``tracking``.
        push_last_successful: The time of the last event push, or None.
        push_successful: The number of successful event pushes.
        push_failed: The number of failed event pushes.
        ntp_active: Whether the time of the sensor comes from NTP.
    """

    name: str
    software: str
    device: str
    uptime: float
    temperature_die: float | None
    temperature_housing: float | None
    illumination_ok: bool
    mode: str
    push_last_successful: str | None
    push_successful: int
    push_failed: int
    ntp_active: bool


def _bucket_json(count: Count) -> Bucket:
    return {
        "start": count.start.isoformat(),
        "entered": count.entered,
        "left": count.left,
    }


def _total_json(entered_left: tuple[int, int]) -> Total:
    return {"entered": entered_left[0], "left": entered_left[1]}


def _hourly(
    client: SensorClient, since: datetime, until: datetime
) -> tuple[Count, ...]:
    try:
        return client.hourly(since, until)
    except SensorError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


def counts_for(client: SensorClient, span: Range, now: datetime) -> Counts:
    """Get the time series of a range that ends now.

    Args:
        client: The sensor client.
        span: ``day`` gives the last 24 hours by hour, ``week`` the last 7
            days by hour, ``month`` the last 30 days by local day.
        now: The current time, timezone-aware.

    Returns:
        The time series. The last bucket can still be running.
    """
    match span:
        case "day":
            since, granularity = hours_before(start_of_hour(now), 23), "hour"
        case "week":
            since, granularity = hours_before(start_of_hour(now), 7 * 24 - 1), "hour"
        case "month":
            since, granularity = start_of_day(now) - timedelta(days=29), "day"
    hourly = _hourly(client, since, now)
    series = bucket(hourly, start_of_day) if granularity == "day" else hourly
    return {
        "granularity": granularity,
        "buckets": [_bucket_json(count) for count in series],
        "entered": sum(c.entered for c in series),
        "left": sum(c.left for c in series),
    }


def summary_for(client: SensorClient, now: datetime) -> Summary:
    """Get the totals for the overview.

    Args:
        client: The sensor client.
        now: The current time, timezone-aware.

    Returns:
        The totals of today, yesterday, this week and the last 30 days.
    """
    today = start_of_day(now)
    week = start_of_week(now)
    month = today - timedelta(days=29)
    yesterday = start_of_day(today - timedelta(hours=12))
    hourly = _hourly(client, min(week, month, yesterday), now)
    end = now + timedelta(hours=1)
    busiest = max(
        (c for c in hourly if c.start >= today and c.entered + c.left > 0),
        key=lambda c: c.entered + c.left,
        default=None,
    )
    return {
        "today": _total_json(total(hourly, today, end)),
        "yesterday": _total_json(total(hourly, yesterday, today)),
        "week": _total_json(total(hourly, week, end)),
        "last_30_days": _total_json(total(hourly, month, end)),
        "busiest_hour": busiest.start.isoformat() if busiest else None,
    }


@router.get("/counts")
def get_counts(span: Range = "day") -> Counts:
    """Get the persons that went in and out over time.

    Args:
        span: The range: ``day``, ``week`` or ``month``.

    Returns:
        The time series.
    """
    return counts_for(SENSOR, span, datetime.now(TIMEZONE))


@router.get("/summary")
def get_summary() -> Summary:
    """Get the totals of today, yesterday, this week and the last 30 days.

    Returns:
        The totals.
    """
    return summary_for(SENSOR, datetime.now(TIMEZONE))


@router.get("/health")
def get_health() -> Health:
    """Get the health of the sensor.

    Returns:
        The status, or 502 if the sensor does not answer.
    """
    try:
        status = SENSOR.status()
    except SensorError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {
        "name": status.name,
        "software": status.software,
        "device": status.device,
        "uptime": status.uptime,
        "temperature_die": status.temperature_die,
        "temperature_housing": status.temperature_housing,
        "illumination_ok": status.illumination_ok,
        "mode": status.mode,
        "push_last_successful": status.push_last_successful,
        "push_successful": status.push_successful,
        "push_failed": status.push_failed,
        "ntp_active": status.ntp_active,
    }


@router.get("/heatmap", response_class=Response)
def get_heatmap() -> Response:
    """Get the heat map of the sensor over its camera image.

    The image is turned by 180 degrees, as the camera image of the live view.
    The sensor clears the heat map when it starts.

    Returns:
        The PNG image, or 502 if the sensor does not answer.
    """
    try:
        png = SENSOR.heatmap()
    except SensorError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    image = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=502, detail="The heat map is not an image.")
    ok, encoded = cv2.imencode(".png", cv2.flip(image, -1))
    if not ok:
        raise HTTPException(status_code=500, detail="The heat map was not encoded.")
    return Response(
        content=encoded.tobytes(),
        media_type="image/png",
        headers={"Cache-Control": "max-age=300"},
    )
