"""Read the counts, the status and the heat map from the HTTP API of the sensor.

The sensor (Xovis PC2-L, software 3.8) has no API description of its own. The
paths and parameters here come from its web UI. The client sends GET requests
to a fixed set of read-only paths only, because some other paths of the sensor
act even on GET (for example ``/api/sensor/reset``), and some need no login.

The sensor counts persons on line 0 ("Ein-/Ausgang"). "Forward" is "in", and
"backward" is "out". The other line of the sensor only makes the push events,
and its counts are not persons.
"""

import csv
import io
import os
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, tzinfo
from itertools import accumulate, groupby
from typing import Final
from xml.etree import ElementTree

import requests

XOVIS_URL: Final = os.getenv("XOVIS_URL", "http://10.0.0.250")
"""The base URL of the sensor."""

XOVIS_AUTH: Final = (
    os.getenv("XOVIS_USER", "admin"),
    os.getenv("XOVIS_PASSWORD", "pass"),
)
"""The HTTP basic credentials of the sensor. The nginx proxy of ``/live`` uses
the same ones."""

COUNT_LINE: Final = 0
"""The count line that counts the persons that go through the gangway."""


@dataclass(frozen=True)
class Count:
    """The crossings of the count line in one time bucket.

    Attributes:
        start: The start of the bucket, timezone-aware.
        entered: The persons that crossed the line forward.
        left: The persons that crossed the line backward.
    """

    start: datetime
    entered: int
    left: int


@dataclass(frozen=True)
class SensorStatus:
    """The health of the sensor.

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


class SensorError(Exception):
    """The sensor did not answer, or it answered with an error."""


def parse_counts(text: str, tz: tzinfo | None = None) -> tuple[Count, ...]:
    """Parse the CSV of ``/api/count-data/select/csv``.

    Args:
        text: The CSV with the columns ``timestamp`` (epoch milliseconds),
            ``forward-count`` and ``backward-count``.
        tz: The timezone of the bucket starts. None gives UTC.

    Returns:
        The buckets in the order of the CSV.

    Raises:
        SensorError: If the text is not the expected CSV.
    """
    reader = csv.DictReader(io.StringIO(text.strip()))
    if reader.fieldnames != ["timestamp", "forward-count", "backward-count"]:
        raise SensorError(f"Unexpected count data: {text[:200]!r}")
    try:
        return tuple(
            Count(
                start=datetime.fromtimestamp(int(row["timestamp"]) / 1000, tz or UTC),
                entered=int(row["forward-count"]),
                left=int(row["backward-count"]),
            )
            for row in reader
        )
    except (KeyError, ValueError, TypeError) as error:
        raise SensorError(f"Unexpected count data: {text[:200]!r}") from error


def start_of_hour(moment: datetime) -> datetime:
    """Get the start of the hour of a time.

    Args:
        moment: The time.

    Returns:
        The time with minutes, seconds and microseconds set to 0.
    """
    return moment.replace(minute=0, second=0, microsecond=0)


def hours_before(moment: datetime, hours: int) -> datetime:
    """Go back a number of real hours from a time.

    Python adds a timedelta to an aware time on the wall clock, so a day with
    a change of the summer time would be one hour off. The function counts in
    UTC instead.

    Args:
        moment: The time, timezone-aware.
        hours: The number of hours.

    Returns:
        The earlier time, in the timezone of ``moment``.
    """
    return (moment.astimezone(UTC) - timedelta(hours=hours)).astimezone(moment.tzinfo)


def start_of_day(moment: datetime) -> datetime:
    """Get the start of the local day of a time.

    Args:
        moment: The time, in the timezone of the day.

    Returns:
        Midnight at the start of the day, in the same timezone.
    """
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def start_of_week(moment: datetime) -> datetime:
    """Get the start of the week (Monday) of a time.

    Args:
        moment: The time, in the timezone of the week.

    Returns:
        Midnight at the start of the Monday, in the same timezone.
    """
    return start_of_day(moment - timedelta(days=moment.weekday()))


def bucket(
    counts: Iterable[Count], start_of: Callable[[datetime], datetime]
) -> tuple[Count, ...]:
    """Sum hourly counts into larger buckets.

    Args:
        counts: The counts, sorted by start.
        start_of: The function that gives the start of the bucket of a time,
            for example `start_of_day`.

    Returns:
        One count for each bucket that holds at least one input count.
    """
    groups = (
        (start, tuple(items))
        for start, items in groupby(counts, key=lambda c: start_of(c.start))
    )
    return tuple(
        Count(start, sum(c.entered for c in group), sum(c.left for c in group))
        for start, group in groups
    )


EMPTY_HOUR: Final = 4
"""The local hour at which the room is assumed to be empty, for `occupancy`."""


def occupancy_day(moment: datetime) -> date:
    """Get the day of a time for `occupancy`, which starts at `EMPTY_HOUR`.

    Args:
        moment: The time, in the local timezone.

    Returns:
        The date of the occupancy day. The hours before `EMPTY_HOUR` belong to
        the day before.
    """
    return (moment - timedelta(hours=EMPTY_HOUR)).date()


def occupancy(counts: Iterable[Count]) -> tuple[int, ...]:
    """Estimate the persons in the room at the end of each hour.

    The estimate adds the persons that went in and takes away the persons
    that went out. It never goes below 0, and it starts at 0 at
    `EMPTY_HOUR` each day, so a missed crossing does not stay. Within an
    hour, a person who goes in and out again does not count.

    Args:
        counts: The hourly counts, sorted by start.

    Returns:
        The estimate for each count, in the same order.
    """

    def step(acc: tuple[date | None, int], count: Count) -> tuple[date | None, int]:
        day, inside = acc
        today = occupancy_day(count.start)
        base = inside if today == day else 0
        return today, max(0, base + count.entered - count.left)

    return tuple(
        inside for _day, inside in accumulate(counts, step, initial=(None, 0))
    )[1:]


def total(counts: Iterable[Count], since: datetime, until: datetime) -> tuple[int, int]:
    """Sum the counts whose bucket starts in a time range.

    Args:
        counts: The counts.
        since: The start of the range, inclusive.
        until: The end of the range, exclusive.

    Returns:
        The persons that entered and the persons that left.
    """
    selected = [c for c in counts if since <= c.start < until]
    return sum(c.entered for c in selected), sum(c.left for c in selected)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _texts(xml: str) -> dict[str, list[tuple[dict[str, str], str]]]:
    """Index the elements of an XML document by their name without namespace."""
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as error:
        raise SensorError(f"Unexpected XML: {xml[:200]!r}") from error
    index: dict[str, list[tuple[dict[str, str], str]]] = {}
    for element in root.iter():
        index.setdefault(_local_name(element.tag), []).append(
            (dict(element.attrib), (element.text or "").strip())
        )
    return index


def _first(index: dict[str, list[tuple[dict[str, str], str]]], name: str) -> str:
    return next((text for _attrs, text in index.get(name, [])), "")


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def parse_status(status_xml: str, info_xml: str) -> SensorStatus:
    """Parse the XML of ``/api/info/status`` and ``/api/info``.

    Args:
        status_xml: The status document.
        info_xml: The info document.

    Returns:
        The health of the sensor. A missing value gives a neutral default.
    """
    status, info = _texts(status_xml), _texts(info_xml)
    temperatures = {
        attrs.get("type", ""): _number(text)
        for attrs, text in status.get("temperature", [])
    }
    versions = {attrs.get("type", ""): text for attrs, text in info.get("version", [])}
    return SensorStatus(
        name=_first(info, "name"),
        software=versions.get("SW", ""),
        device=_first(info, "device-type"),
        uptime=(_number(_first(status, "uptime")) or 0) / 1000,
        temperature_die=temperatures.get("die"),
        temperature_housing=temperatures.get("housing"),
        illumination_ok=_first(status, "sufficientIllumination") == "true",
        mode=_first(status, "mode"),
        push_last_successful=_first(status, "last-successful") or None,
        push_successful=int(_number(_first(status, "nb-successful")) or 0),
        push_failed=int(_number(_first(status, "nb-unsuccessful")) or 0),
        ntp_active=_first(status, "active") == "true",
    )


type Fetch = Callable[[str, dict[str, str]], requests.Response]


def _fetch(path: str, params: dict[str, str]) -> requests.Response:
    return requests.get(
        f"{XOVIS_URL}{path}", params=params, auth=XOVIS_AUTH, timeout=10
    )


class SensorClient:
    """Read the sensor, with a short cache for each request.

    The sensor needs up to a few seconds for a heat map, and the frontend
    polls. The cache keeps the load on the sensor low.
    """

    def __init__(
        self, fetch: Fetch = _fetch, clock: Callable[[], float] = time.monotonic
    ) -> None:
        """Create the client.

        Args:
            fetch: The function that sends a GET request to a sensor path.
            clock: The clock of the cache, in seconds.
        """
        self._fetch = fetch
        self._clock = clock
        self._lock = threading.Lock()
        self._cache: dict[
            tuple[str, tuple[tuple[str, str], ...]], tuple[float, bytes]
        ] = {}

    def _get(self, path: str, params: dict[str, str], ttl: float) -> bytes:
        key = (path, tuple(sorted(params.items())))
        now = self._clock()
        with self._lock:
            hit = self._cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
        try:
            response = self._fetch(path, params)
            response.raise_for_status()
        except requests.RequestException as error:
            raise SensorError(f"The sensor did not answer {path}: {error}") from error
        with self._lock:
            self._cache[key] = (now, response.content)
        return response.content

    def hourly(self, since: datetime, until: datetime) -> tuple[Count, ...]:
        """Get the hourly counts of the count line.

        Args:
            since: The start of the range, timezone-aware.
            until: The end of the range, timezone-aware.

        Returns:
            One count for each hour, in the timezone of ``since``. The last
            hour can still be running.
        """
        params = {
            "from": str(int(since.timestamp() * 1000)),
            "to": str(int(until.timestamp() * 1000)),
            "granularity": "ONE_HOUR",
            "count-line": str(COUNT_LINE),
        }
        text = self._get("/api/count-data/select/csv", params, ttl=60).decode()
        return parse_counts(text, since.tzinfo)

    def status(self) -> SensorStatus:
        """Get the health of the sensor.

        Returns:
            The status. The values are at most 30 s old.
        """
        status = self._get("/api/info/status", {}, ttl=30).decode()
        info = self._get("/api/info", {}, ttl=3600).decode()
        return parse_status(status, info)

    def heatmap(self) -> bytes:
        """Get the heat map over the camera image.

        Returns:
            The PNG image. It holds the positions since the last start of the
            sensor, and it is at most 5 minutes old.
        """
        params = {"min-sat": "0", "max-sat": "100"}
        return self._get("/api/maps/heat/export", params, ttl=300)


SENSOR: Final = SensorClient()
"""The client that the API uses."""
