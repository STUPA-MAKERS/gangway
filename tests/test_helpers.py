"""Tests for the helper functions."""

import math

import pytest
from rpi_ws2805 import RGBCCT

from gangway.helpers import (
    AnimationFactory,
    interpolate_points,
    interpolate_rgbcct,
    parse_animation,
    sign,
    to_hex,
)
from gangway.types import Point, YamlValue


def test_sign() -> None:
    """Sign gives -1, 0 or 1, and always 0 if disabled."""
    assert sign(5, True) == 1
    assert sign(-5, True) == -1
    assert sign(0, True) == 0
    assert sign(5, False) == 0
    assert sign(-5, False) == 0


def test_interpolate_rgbcct() -> None:
    """Interpolation mixes the channels and applies the sign step."""
    c1 = RGBCCT(0, 0, 0, 0, 0)
    c2 = RGBCCT(100, 100, 100, 100, 100)

    res = interpolate_rgbcct(c1, c2, 0.5, use_sign=False)
    assert res.r == 50
    assert res.g == 50

    # c2 - c1 is positive, so the sign step subtracts 1.
    assert interpolate_rgbcct(c1, c2, 0.5, use_sign=True).r == 49
    assert interpolate_rgbcct(c2, c1, 0.5, use_sign=True).r == 51


def test_interpolate_points() -> None:
    """The first of ten parts of a line has its center at 5 percent."""
    # Point subtraction is reversed (other - self), so p1 - p2 is p2 - p1.
    res = interpolate_points(Point(0, 0), Point(10, 10), 10, 0)
    assert math.isclose(res.x, 0.5)
    assert math.isclose(res.y, 0.5)


def test_to_hex() -> None:
    """The hex color holds the RGB channels."""
    assert to_hex(RGBCCT(255, 0, 128, 0, 0)) == "#ff0080"
    assert to_hex(RGBCCT(10, 20, 30, 0, 0)) == "#0a141e"


def test_parse_animation_simple_color() -> None:
    """A mapping with r, g and b is a color."""
    res = parse_animation({"r": 255, "g": 0, "b": 0, "ww": 0, "cw": 0}, {})
    assert isinstance(res, RGBCCT)
    assert res.r == 255


def test_parse_animation_function() -> None:
    """The config calls a function with scalar, keyword and nested arguments."""

    def my_anim(color: object, brightness: float = 1.0) -> tuple[object, float]:
        return (color, brightness)

    funcs: dict[str, AnimationFactory] = {"my_anim": my_anim}

    assert parse_animation({"my_anim": "red"}, funcs) == ("red", 1.0)
    assert parse_animation(
        {"my_anim": {"color": "blue", "brightness": 0.5}}, funcs
    ) == ("blue", 0.5)
    assert parse_animation(
        {"my_anim": {"color": {"r": 10, "g": 10, "b": 10}, "brightness": 0.5}},
        funcs,
    ) == (RGBCCT(10, 10, 10), 0.5)


def test_parse_animation_unknown_function() -> None:
    """An unknown function name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown animation function"):
        parse_animation({"unknown": {}}, {})


def test_parse_animation_unknown_param() -> None:
    """An unknown parameter name raises ValueError."""

    def my_anim(val: object) -> object:
        return val

    with pytest.raises(ValueError, match="Unknown parameter"):
        parse_animation({"my_anim": {"invalid_param": 1}}, {"my_anim": my_anim})


def test_parse_animation_var_positional() -> None:
    """A list for a variadic parameter gives the positional arguments."""

    def my_seq(*args: object) -> list[object]:
        return list(args)

    assert parse_animation({"seq": {"args": ["a", "b"]}}, {"seq": my_seq}) == [
        "a",
        "b",
    ]


def test_parse_animation_by_strip_structure() -> None:
    """Nested strip assignments parse to tuples with parsed colors."""

    def mock_by_strip(
        assignments: object = None, default: object = None
    ) -> dict[str, object]:
        return {"type": "by_strip", "assignments": assignments, "default": default}

    def mock_strip_assignment(strip: int, animation: object) -> tuple[int, object]:
        return (strip, animation)

    funcs: dict[str, AnimationFactory] = {
        "by_strip": mock_by_strip,
        "strip_assignment": mock_strip_assignment,
    }

    config: YamlValue = {
        "by_strip": {
            "assignments": [
                {
                    "strip_assignment": {
                        "strip": 1,
                        "animation": {"r": 255, "g": 0, "b": 0, "ww": 0, "cw": 0},
                    }
                },
                {
                    "strip_assignment": {
                        "strip": 2,
                        "animation": {"r": 0, "g": 255, "b": 0, "ww": 0, "cw": 0},
                    }
                },
            ],
            "default": {"r": 0, "g": 0, "b": 255, "ww": 0, "cw": 0},
        }
    }

    assert parse_animation(config, funcs) == {
        "type": "by_strip",
        "assignments": [(1, RGBCCT(255, 0, 0, 0, 0)), (2, RGBCCT(0, 255, 0, 0, 0))],
        "default": RGBCCT(0, 0, 255, 0, 0),
    }
