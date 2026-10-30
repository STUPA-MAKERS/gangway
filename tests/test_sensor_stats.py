"""Tests for the sensor statistics, with recorded sensor responses."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import cv2
import numpy as np
import pytest
import requests

from gangway.api.stats import counts_for, prepare_heatmap, summary_for
from gangway.xovis.sensor_api import (
    Count,
    SensorClient,
    SensorError,
    bucket,
    occupancy,
    parse_counts,
    parse_status,
    start_of_day,
    start_of_week,
)

BERLIN = ZoneInfo("Europe/Berlin")

STATUS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<status xmlns:ns2="http://www.xovis.com/common-types" xmlns="http://www.xovis.com/status"
  xmlns:ns3="http://www.xovis.com/operation">
  <sensor-time>2026-10-30T23:29:55+01:00</sensor-time>
  <uptime>177043120</uptime>
  <request-status><ns2:status>OK</ns2:status></request-status>
  <temperatures>
    <temperature type="die">50.0</temperature>
    <temperature type="housing">51.0</temperature>
  </temperatures>
  <illumination><gain>7.5</gain><sufficientIllumination>true</sufficientIllumination>
  </illumination>
  <operation><ns3:mode>tracking</ns3:mode></operation>
  <data-push-agents><push-agent id="0">
    <last-successful>2026-10-30T23:29:37+01:00</last-successful>
    <nb-successful>174368</nb-successful><nb-unsuccessful>3</nb-unsuccessful>
  </push-agent></data-push-agents>
  <ntp-status><active>true</active></ntp-status>
</status>"""

INFO_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<info xmlns:ns2="http://www.xovis.com/common-types" xmlns="http://www.xovis.com/info">
  <versions><version type="HW">E</version><version type="SW">3.8.1 (0fd7f43)</version>
  </versions>
  <name>G.A.N.G.W.A.Y</name>
  <device-type class="COUNTER_2">PC2 - L</device-type>
</info>"""


def _csv(start: datetime, rows: list[tuple[int, int]]) -> str:
    first = start.astimezone(UTC)
    lines = [
        f"{int((first + timedelta(hours=i)).timestamp() * 1000)},{a},{b}"
        for i, (a, b) in enumerate(rows)
    ]
    return "timestamp,forward-count,backward-count\n" + "\n".join(lines) + "\n"


class _Response(requests.Response):
    def __init__(self, body: str, status: int = 200) -> None:
        super().__init__()
        self._content = body.encode()
        self.status_code = status


class _Sensor:
    """A fake sensor that answers the count CSV with one count per hour."""

    def __init__(self, per_hour: int = 1) -> None:
        self.per_hour = per_hour
        self.calls: list[str] = []

    def __call__(self, path: str, params: dict[str, str]) -> requests.Response:
        self.calls.append(path)
        since, until = int(params["from"]), int(params["to"])
        start = datetime.fromtimestamp(since / 1000, BERLIN)
        hours = (until - since) // 3_600_000 + 1
        return _Response(_csv(start, [(self.per_hour, self.per_hour)] * hours))


def test_parse_counts_reads_the_csv_of_the_sensor() -> None:
    """The CSV gives one count for each hour, in the requested timezone."""
    text = "timestamp,forward-count,backward-count\n1793358000000,11,10\n"

    (count,) = parse_counts(text, BERLIN)

    assert count == Count(datetime(2026, 10, 30, 12, tzinfo=BERLIN), 11, 10)


def test_parse_counts_refuses_an_error_text() -> None:
    """An error text of the sensor is not count data."""
    with pytest.raises(SensorError):
        parse_counts("Error 400, unknown command")


def test_bucket_sums_hours_by_local_day_across_the_dst_change() -> None:
    """The night of the change to winter time has 25 hours, all in one day."""
    start = datetime(2026, 10, 25, 0, tzinfo=BERLIN)
    hourly = parse_counts(_csv(start, [(1, 2)] * 26), BERLIN)

    days = bucket(hourly, start_of_day)

    assert [(d.start.day, d.entered, d.left) for d in days] == [
        (25, 25, 50),
        (26, 1, 2),
    ]


def test_start_of_week_is_monday_midnight() -> None:
    """A Friday goes back to the Monday of its week."""
    friday = datetime(2026, 10, 30, 15, 12, tzinfo=BERLIN)

    assert start_of_week(friday) == datetime(2026, 10, 26, tzinfo=BERLIN)


def test_parse_status_reads_the_status_and_the_info() -> None:
    """The status values come from both documents, without namespaces."""
    status = parse_status(STATUS_XML, INFO_XML)

    assert status.name == "G.A.N.G.W.A.Y"
    assert status.software == "3.8.1 (0fd7f43)"
    assert status.device == "PC2 - L"
    assert round(status.uptime, 2) == 177043.12
    assert status.temperature_die == 50.0
    assert status.temperature_housing == 51.0
    assert status.illumination_ok
    assert status.mode == "tracking"
    assert status.push_successful == 174368
    assert status.push_failed == 3
    assert status.ntp_active


def test_counts_for_a_month_gives_one_bucket_per_day() -> None:
    """The month range sums the hours of the sensor into 30 local days."""
    now = datetime(2026, 10, 30, 15, 30, tzinfo=BERLIN)

    counts = counts_for(SensorClient(fetch=_Sensor()), "month", now)

    assert counts["granularity"] == "day"
    assert len(counts["buckets"]) == 30
    assert counts["buckets"][-1]["start"] == "2026-10-30T00:00:00+01:00"
    assert counts["buckets"][-1]["entered"] == 16


def test_summary_for_sums_today_and_the_week() -> None:
    """Today has 16 hours until 15:30, and the week started on Monday."""
    now = datetime(2026, 10, 30, 15, 30, tzinfo=BERLIN)

    summary = summary_for(SensorClient(fetch=_Sensor()), now)

    assert summary["today"] == {"entered": 16, "left": 16}
    assert summary["yesterday"] == {"entered": 24, "left": 24}
    assert summary["week"] == {"entered": 4 * 24 + 16, "left": 4 * 24 + 16}


def test_client_caches_a_request() -> None:
    """A second request within the cache time does not reach the sensor."""
    sensor = _Sensor()
    clock = iter([0.0, 10.0, 100.0])
    client = SensorClient(fetch=sensor, clock=lambda: next(clock))
    since = datetime(2026, 10, 30, tzinfo=BERLIN)

    client.hourly(since, since + timedelta(hours=1))
    client.hourly(since, since + timedelta(hours=1))
    client.hourly(since, since + timedelta(hours=1))

    assert len(sensor.calls) == 2


def test_client_reports_an_unreachable_sensor() -> None:
    """A connection error becomes a SensorError."""

    def offline(_path: str, _params: dict[str, str]) -> requests.Response:
        raise requests.ConnectionError("no route to host")

    with pytest.raises(SensorError):
        SensorClient(fetch=offline).status()


def test_prepare_heatmap_crops_the_frame_and_turns_the_picture() -> None:
    """The transparent frame goes away, and the picture turns by 180 degrees."""
    image = np.zeros((6, 8, 4), np.uint8)
    image[:, :, :3] = 255
    image[1:5, 2:6] = (0, 0, 255, 255)
    image[1, 2] = (255, 0, 0, 255)
    png = cv2.imencode(".png", image)[1].tobytes()

    result = cv2.imdecode(
        np.frombuffer(prepare_heatmap(png), np.uint8), cv2.IMREAD_UNCHANGED
    )

    assert result is not None
    pixels: list[list[list[int]]] = result.tolist()
    assert result.shape == (4, 4, 3)
    assert pixels[3][3] == [255, 0, 0]
    assert pixels[0][0] == [0, 0, 255]


def test_occupancy_adds_in_takes_out_and_never_goes_below_zero() -> None:
    """More persons out than in keeps the estimate at 0."""
    start = datetime(2026, 10, 30, 10, tzinfo=BERLIN)
    hourly = parse_counts(_csv(start, [(5, 1), (2, 3), (0, 9), (4, 0)]), BERLIN)

    assert occupancy(hourly) == (4, 3, 0, 4)


def test_occupancy_starts_at_zero_at_four_in_the_morning() -> None:
    """A person who was not counted out does not stay in the next day."""
    start = datetime(2026, 10, 30, 2, tzinfo=BERLIN)
    hourly = parse_counts(_csv(start, [(3, 0), (0, 0), (1, 0)]), BERLIN)

    assert occupancy(hourly) == (3, 3, 1)


def test_counts_for_days_gives_the_peak_of_the_estimate() -> None:
    """A day bucket holds the highest hourly estimate of its day."""
    now = datetime(2026, 10, 30, 15, 30, tzinfo=BERLIN)

    counts = counts_for(SensorClient(fetch=_Sensor()), "month", now)

    assert all(b["occupancy"] == 0 for b in counts["buckets"])


def test_summary_has_all_time_and_the_room_estimate() -> None:
    """All time sums every hour of the sensor."""
    now = datetime(2026, 10, 30, 15, 30, tzinfo=BERLIN)

    summary = summary_for(SensorClient(fetch=_Sensor(per_hour=2)), now)

    assert summary["all_time"]["entered"] > summary["last_30_days"]["entered"]
    assert summary["in_room"] == 0
