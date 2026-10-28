"""Tests for the idle animations."""

import pytest
from rpi_ws2805 import RGBCCT

from gangway.animations.idle import (
    fire,
    idle,
    linear_rainbow,
    rainbow,
    sparkle,
    static,
    wave,
)
from gangway.types import LED, Axis, Point, Rectangle, SceneContext, TrackedPoint


@pytest.fixture
def led() -> LED:
    """Get an LED at the center of the floor."""
    return LED(index=0, p=Point(50, 50))


@pytest.fixture
def ctx(led: LED) -> SceneContext:
    """Get a 100 x 100 floor with one LED."""
    return SceneContext(floor=Rectangle(Point(0, 0), Point(100, 100)), leds=[led])


def test_static(ctx: SceneContext, led: LED) -> None:
    """Static returns its color."""
    color = RGBCCT(255, 0, 0)
    assert static(color)(0.0, ctx, led, []) == color


def test_rainbow(ctx: SceneContext, led: LED) -> None:
    """Rainbow gives red at hue 0."""
    # x_norm is 0.5 and spread is 2, so the hue is 1.0, which wraps to 0.
    res = rainbow(speed=0.1, spread=2.0)(0.0, ctx, led, [])
    assert (res.r, res.g, res.b) == (255, 0, 0)


@pytest.mark.parametrize("direction", ["x", "y"])
def test_linear_rainbow(ctx: SceneContext, led: LED, direction: str) -> None:
    """Linear rainbow gives cyan at the center of the floor."""
    anim = linear_rainbow(direction=Axis(direction), speed=0.0, spread=1.0)
    res = anim(0.0, ctx, led, [])
    assert (res.r, res.g, res.b) == (0, 255, 255)


def test_idle_animation_switching(ctx: SceneContext, led: LED) -> None:
    """Idle selects the animation from the presence of persons."""
    idle_color = RGBCCT(10, 10, 10)
    active_color = RGBCCT(255, 255, 255)
    anim = idle(static(idle_color), static(active_color))

    assert anim(0.0, ctx, led, []) == idle_color
    assert anim(0.0, ctx, led, [TrackedPoint(10, 10)]) == active_color


def test_fire(ctx: SceneContext, led: LED) -> None:
    """Fire only dims the base color."""
    res = fire(base_color=RGBCCT(200, 100, 0), flicker_speed=0.1)(0.0, ctx, led, [])
    assert isinstance(res, RGBCCT)
    assert res.r <= 200
    assert res.g <= 100
    assert res.b == 0


def test_sparkle(ctx: SceneContext, led: LED) -> None:
    """Sparkle returns a color."""
    res = sparkle(density=0.5, speed=1.0)(0.0, ctx, led, [])
    assert isinstance(res, RGBCCT)


def test_wave(ctx: SceneContext, led: LED) -> None:
    """Wave only uses the channels of its colors."""
    res = wave(colors=[RGBCCT(255, 0, 0)], n_waves=1)(0.0, ctx, led, [])
    assert 0 <= res.r <= 255
    assert res.g == 0
    assert res.b == 0


def test_rainbow_on_a_floor_with_no_width(led: LED) -> None:
    """Rainbow gives a color on a floor with zero width, not an error."""
    flat = SceneContext(floor=Rectangle(Point(50, 0), Point(50, 100)), leds=[led])
    assert isinstance(rainbow()(0.0, flat, led, []), RGBCCT)
