"""The `schedule` and `day_of_week` animations."""

import datetime
from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import (
    LED,
    Animation,
    AnimationOrColor,
    SceneContext,
    TrackedPoint,
)


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

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        now = datetime.datetime.now().time()
        try:
            start_t = datetime.time.fromisoformat(start)
            end_t = datetime.time.fromisoformat(end)
        except ValueError:
            start_t = datetime.time(18, 0)
            end_t = datetime.time(6, 0)

        if start_t <= end_t:
            is_active = start_t <= now <= end_t
        else:
            is_active = now >= start_t or now <= end_t

        target = primary if is_active else secondary

        if isinstance(target, RGBCCT):
            return target

        return target(time, ctx, led, objects)

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
    days = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        weekday = datetime.datetime.now().weekday()
        anim = days[weekday]

        if isinstance(anim, RGBCCT):
            return anim
        return anim(time, ctx, led, objects)

    return animation
