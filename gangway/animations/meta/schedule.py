"""The `schedule` and `day_of_week` animations."""

import datetime
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...helpers import render
from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)

_DEFAULT_WINDOW = (datetime.time(18, 0), datetime.time(6, 0))


def _window(start: object, end: object) -> tuple[datetime.time, datetime.time]:
    """Parse a time range.

    A value that is not a valid ``HH:MM`` string gives `_DEFAULT_WINDOW`.
    This includes the integer that a YAML 1.1 loader makes of an unquoted
    ``18:00``.
    """
    match start, end:
        case str(), str():
            try:
                return (
                    datetime.time.fromisoformat(start),
                    datetime.time.fromisoformat(end),
                )
            except ValueError:
                return _DEFAULT_WINDOW
        case _:
            return _DEFAULT_WINDOW


def _in_window(now: datetime.time, start: datetime.time, end: datetime.time) -> bool:
    """Check if a time is in a range. The range can go past midnight."""
    return start <= now <= end if start <= end else now >= start or now <= end


def schedule(
    primary: AnimationOrColor,
    secondary: AnimationOrColor,
    start: str = "18:00",
    end: str = "06:00",
) -> Animation:
    """Show ``primary`` between two times of the day, else ``secondary``.

    The time range can go past midnight.

    Args:
        primary: The animation inside the time range.
        secondary: The animation outside the time range.
        start: The start time as ``HH:MM``.
        end: The end time as ``HH:MM``.

    Returns:
        The animation. An invalid time gives the range 18:00 to 06:00.
    """
    window = _window(start, end)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        now = datetime.datetime.now().time()
        active = _in_window(now, *window)
        return render(primary if active else secondary, time, ctx, led, objects)

    return animation


def day_of_week(
    monday: AnimationOrColor = RGBCCT(),
    tuesday: AnimationOrColor = RGBCCT(),
    wednesday: AnimationOrColor = RGBCCT(),
    thursday: AnimationOrColor = RGBCCT(),
    friday: AnimationOrColor = RGBCCT(),
    saturday: AnimationOrColor = RGBCCT(),
    sunday: AnimationOrColor = RGBCCT(),
) -> Animation:
    """Show a different animation on each day of the week.

    Args:
        monday: The animation on Monday.
        tuesday: The animation on Tuesday.
        wednesday: The animation on Wednesday.
        thursday: The animation on Thursday.
        friday: The animation on Friday.
        saturday: The animation on Saturday.
        sunday: The animation on Sunday.

    Returns:
        The animation.
    """
    days = (monday, tuesday, wednesday, thursday, friday, saturday, sunday)

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return render(days[datetime.datetime.now().weekday()], time, ctx, led, objects)

    return animation
