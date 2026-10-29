"""Tests for the meta and responsive animations."""

import datetime
from collections.abc import Callable, Sequence
from typing import ClassVar, Self, cast

import pytest
from rpi_ws2805 import RGBCCT

from gangway.animations.idle import static
from gangway.animations.meta import (
    alternate,
    blend,
    by_strip,
    extrapolate,
    persist,
    proximity,
    proximity_speed,
    schedule,
    smooth,
    strip_assignment,
)
from gangway.animations.responsive import dot, exponential, paint
from gangway.types import (
    LED,
    BlendMode,
    Point,
    Rectangle,
    SceneContext,
    SpeedMode,
    TrackedPoint,
)

RED = RGBCCT(r=255)
GREEN = RGBCCT(g=255)
BLUE = RGBCCT(b=100)


@pytest.fixture
def led() -> LED:
    """Get an LED at the center of the floor."""
    return LED(index=0, p=Point(50, 50))


@pytest.fixture
def ctx(led: LED) -> SceneContext:
    """Get a 100 x 100 floor with one LED."""
    return SceneContext(floor=Rectangle(Point(0, 0), Point(100, 100)), leds=[led])


def test_blend_average_and_max(ctx: SceneContext, led: LED) -> None:
    """Blend mixes each channel by the mean or by the maximum."""
    assert blend(RED, BLUE)(0.0, ctx, led, []) == RGBCCT(r=127, b=50)
    assert blend(RED, BLUE, mode=BlendMode.MAX)(0.0, ctx, led, []) == RGBCCT(
        r=255, b=100
    )


def test_blend_without_animations_is_off(ctx: SceneContext, led: LED) -> None:
    """Blend with no animations turns the LED off."""
    assert blend()(0.0, ctx, led, []) == RGBCCT()


def test_alternate_steps_through_animations(ctx: SceneContext, led: LED) -> None:
    """Alternate shows each animation for one time slot, then starts again."""
    anim = alternate(RED, static(GREEN), BLUE, length=1.0)
    colors = [anim(t, ctx, led, []) for t in (0.5, 1.5, 2.5, 3.5)]
    assert colors == [RED, GREEN, BLUE, RED]
    assert alternate()(0.0, ctx, led, []) == RGBCCT()


def test_by_strip_uses_default_for_other_strips(ctx: SceneContext) -> None:
    """By strip uses the assignment of the strip, else the default."""
    anim = by_strip([strip_assignment(1, RED)], default=GREEN)
    assert anim(0.0, ctx, LED(0, Point(), strip_index=1), []) == RED
    assert anim(0.0, ctx, LED(1, Point(), strip_index=0), []) == GREEN


def test_dot_and_exponential_use_distance(ctx: SceneContext, led: LED) -> None:
    """Dot and exponential select the color from the closest person."""
    near = [TrackedPoint(55, 50)]
    far = [TrackedPoint(500, 500)]
    assert dot(RED, GREEN, radius=10)(0.0, ctx, led, near) == RED
    assert dot(RED, GREEN, radius=10)(0.0, ctx, led, far) == GREEN
    assert exponential(RED, GREEN)(0.0, ctx, led, []) == GREEN
    assert exponential(RED, GREEN, radius=1)(0.0, ctx, led, [TrackedPoint(50, 50)]) == (
        RED
    )


def test_paint_keeps_the_path(ctx: SceneContext, led: LED) -> None:
    """Paint keeps a position lit for the persistence time."""
    anim = paint(RED, GREEN, radius=10, persistence=1.0)
    assert anim(0.0, ctx, led, [TrackedPoint(50, 50)]) == RED
    assert anim(0.5, ctx, led, []) == RED
    assert anim(2.0, ctx, led, []) == GREEN


def test_persist_keeps_a_person_for_a_short_time(ctx: SceneContext, led: LED) -> None:
    """Persist keeps a lost person for the grace time only."""
    anim = persist(dot(RED, GREEN, radius=10), duration=2.0)
    person = [TrackedPoint(50, 50)]
    assert anim(0.0, ctx, led, person) == RED
    assert anim(0.05, ctx, led, []) == RED
    assert anim(0.5, ctx, led, []) == GREEN


def test_extrapolate_moves_along_the_velocity(ctx: SceneContext, led: LED) -> None:
    """Extrapolate moves a person forward along its measured velocity."""
    anim = extrapolate(dot(RED, GREEN, radius=5), latency=1.0)
    assert anim(0.0, ctx, led, [TrackedPoint(30, 50, id=1, timestamp=0.0)]) == GREEN
    # The person moves 10 units per second to the LED, so one second of
    # latency puts the prediction on the LED.
    assert anim(1.0, ctx, led, [TrackedPoint(40, 50, id=1, timestamp=1.0)]) == RED


def test_proximity_fades_with_distance(ctx: SceneContext, led: LED) -> None:
    """Proximity gives the secondary color with nobody near the point."""
    anim = proximity(RED, GREEN, x=0, y=0, radius=100)
    assert anim(0.0, ctx, led, []) == GREEN
    assert anim(0.0, ctx, led, [TrackedPoint(0, 0)]) == RED


def test_proximity_speed_instances_have_own_clocks(ctx: SceneContext, led: LED) -> None:
    """Each proximity speed animation keeps its own animation time."""
    seen: list[float] = []

    def record(
        time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        seen.append(time)
        return RGBCCT()

    first = proximity_speed(record, radius=100, proximity_factor=0.5)
    second = proximity_speed(record, radius=100, proximity_factor=0.5)
    person = [TrackedPoint(0, 0)]
    _ = first(0.0, ctx, led, person)
    _ = first(1.0, ctx, led, person)
    _ = second(1.0, ctx, led, person)
    # The person at the point doubles the speed of the first animation. The
    # second animation starts at its first frame.
    assert seen == [0.0, 2.0, 1.0]


def test_proximity_speed_rejects_an_invalid_mode(ctx: SceneContext, led: LED) -> None:
    """Proximity speed raises on the first frame with a person."""
    # The YAML config can give any string, so the type check cannot stop it.
    anim = proximity_speed(RED, mode=cast("SpeedMode", "sideways"))
    assert anim(0.0, ctx, led, []) == RED
    with pytest.raises(ValueError, match="Invalid mode"):
        _ = anim(1.0, ctx, led, [TrackedPoint(0, 0)])


def test_schedule_window_past_midnight(
    ctx: SceneContext, led: LED, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Schedule shows the primary animation inside a range past midnight."""

    class FakeDateTime(datetime.datetime):
        now_value: ClassVar[datetime.datetime] = datetime.datetime(2026, 1, 1, 23, 0)

        @classmethod
        def now(cls, tz: datetime.tzinfo | None = None) -> Self:
            return cls.combine(cls.now_value.date(), cls.now_value.time(), tzinfo=tz)

    monkeypatch.setattr(datetime, "datetime", FakeDateTime)
    anim = schedule(RED, GREEN, start="22:00", end="02:00")
    assert anim(0.0, ctx, led, []) == RED
    FakeDateTime.now_value = datetime.datetime(2026, 1, 1, 12, 0)
    assert anim(0.0, ctx, led, []) == GREEN


def test_smooth_averages_over_frames(ctx: SceneContext, led: LED) -> None:
    """Smooth moves the color part of the way to the target in each frame."""
    target = [RGBCCT(r=200), RGBCCT(), RGBCCT()]

    def step(
        _time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return target.pop(0)

    anim = smooth(step, smoothing=0.5)
    assert [anim(t, ctx, led, []).r for t in (0.0, 1.0, 2.0)] == [200, 100, 50]


def _recorder(
    seen: list[float],
) -> Callable[[float, SceneContext, LED, Sequence[TrackedPoint]], RGBCCT]:
    """Get an animation that records the animation time of each call."""

    def record(
        time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        seen.append(time)
        return RGBCCT()

    return record


def test_proximity_speed_at_full_intensity_is_capped(
    ctx: SceneContext, led: LED
) -> None:
    """A person on the point at full strength gives the largest speed factor."""
    seen: list[float] = []
    anim = proximity_speed(_recorder(seen), radius=100, proximity_factor=1.0)
    person = [TrackedPoint(0, 0)]
    _ = anim(0.0, ctx, led, person)
    _ = anim(1.0, ctx, led, person)
    assert seen == [0.0, 100.0]


def test_proximity_speed_applies_multiplier_without_persons(
    ctx: SceneContext, led: LED
) -> None:
    """The multiplier also scales the time steps of frames with nobody."""
    seen: list[float] = []
    anim = proximity_speed(_recorder(seen), multiplier=2.0)
    _ = anim(0.0, ctx, led, [])
    _ = anim(1.0, ctx, led, [])
    assert seen == [0.0, 2.0]


def test_persist_starts_again_after_time_goes_back(ctx: SceneContext, led: LED) -> None:
    """A time before the last frame clears the kept persons."""
    anim = persist(dot(RED, GREEN, radius=10), duration=2.0)
    assert anim(10.0, ctx, led, [TrackedPoint(50, 50)]) == RED
    assert anim(0.0, ctx, led, []) == GREEN


def test_paint_starts_again_after_time_goes_back(ctx: SceneContext, led: LED) -> None:
    """A time before the last frame clears the path and paints again."""
    anim = paint(RED, GREEN, radius=10, persistence=1.0)
    assert anim(10.0, ctx, led, [TrackedPoint(50, 50)]) == RED
    assert anim(0.0, ctx, led, []) == GREEN
    assert anim(0.1, ctx, led, [TrackedPoint(50, 50)]) == RED


@pytest.mark.parametrize(("start", "end"), [(810, 820), (None, "06:00"), ("x", "y")])
def test_schedule_with_an_invalid_range_uses_the_default(
    ctx: SceneContext,
    led: LED,
    monkeypatch: pytest.MonkeyPatch,
    start: object,
    end: object,
) -> None:
    """A range that is not two HH:MM strings gives 18:00 to 06:00."""

    class FakeDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz: datetime.tzinfo | None = None) -> Self:
            return cls(2026, 1, 1, 23, 0, tzinfo=tz)

    monkeypatch.setattr(datetime, "datetime", FakeDateTime)
    anim = schedule(RED, GREEN, start=cast("str", start), end=cast("str", end))
    assert anim(0.0, ctx, led, []) == RED


def test_paint_scene_test_matches_the_single_led_test() -> None:
    """The hit test for all LEDs of a frame matches the test for one LED."""
    leds = [LED(index=i, p=Point(i * 10.0, 50)) for i in range(11)]
    floor = Rectangle(Point(0, 0), Point(100, 100))
    scene = SceneContext(floor=floor, leds=leds)
    alone = SceneContext(floor=floor, leds=[])
    people = [TrackedPoint(20, 50), TrackedPoint(75, 52)]
    in_scene, single = paint(RED, GREEN, radius=10), paint(RED, GREEN, radius=10)

    assert [in_scene(0.0, scene, led, people) for led in leds] == [
        single(0.0, alone, led, people) for led in leds
    ]
    assert in_scene(0.0, scene, leds[2], people) == RED
    assert in_scene(0.0, scene, leds[5], people) == GREEN


def test_extrapolate_predicts_once_per_frame(ctx: SceneContext, led: LED) -> None:
    """All LEDs of a frame get the same predicted persons."""
    seen: list[Sequence[TrackedPoint]] = []

    def record(
        _time: float, _ctx: SceneContext, _led: LED, objects: Sequence[TrackedPoint]
    ) -> RGBCCT:
        seen.append(objects)
        return RED

    anim = extrapolate(record, latency=1.0)
    people = [TrackedPoint(30, 50, id=1, timestamp=0.0)]
    anim(0.0, ctx, led, people)
    anim(0.0, ctx, led, people)
    anim(1.0, ctx, led, people)

    assert seen[0] is seen[1]
    assert seen[2] is not seen[0]
