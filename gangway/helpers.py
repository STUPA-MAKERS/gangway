"""Helper functions for colors, geometry and the animation config."""

import inspect
from collections.abc import Callable, Mapping, Sequence
from typing import NotRequired, TypedDict, TypeGuard, cast

from rpi_ws2805 import RGBCCT

from .types import (
    LED,
    Animation,
    AnimationOrColor,
    Point,
    SceneContext,
    TrackedPoint,
    YamlValue,
)

type AnimationFactory = Callable[..., object]
"""A function that the animation config can call by name."""


class ColorConfig(TypedDict):
    """A color in the animation config.

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
    cw: NotRequired[int]
    ww: NotRequired[int]


def sign(x: float, use_sign: bool) -> int:
    """Get the sign of a number.

    Args:
        x: The number.
        use_sign: Set to False to always get 0.

    Returns:
        -1, 0 or 1. The result is always 0 if ``use_sign`` is False.
    """
    if not use_sign:
        return 0

    return 0 if x == 0 else (-1 if x < 0 else 1)


def interpolate_rgbcct(
    color_a: RGBCCT, color_b: RGBCCT, weight_a: float, use_sign: bool = True
) -> RGBCCT:
    """Mix two colors channel by channel.

    Args:
        color_a: The first color.
        color_b: The second color.
        weight_a: The weight of ``color_a``, from 0 to 1. ``color_b`` gets
            the remaining weight.
        use_sign: Set to True to move each channel one step away from
            ``color_b``. This makes sure that a fade never stops on the
            target value too early.

    Returns:
        The mixed color.
    """
    return RGBCCT(
        r=int(color_a.r * weight_a + color_b.r * (1 - weight_a))
        - sign(color_b.r - color_a.r, use_sign),
        g=int(color_a.g * weight_a + color_b.g * (1 - weight_a))
        - sign(color_b.g - color_a.g, use_sign),
        b=int(color_a.b * weight_a + color_b.b * (1 - weight_a))
        - sign(color_b.b - color_a.b, use_sign),
        ww=int(color_a.ww * weight_a + color_b.ww * (1 - weight_a))
        - sign(color_b.ww - color_a.ww, use_sign),
        cw=int(color_a.cw * weight_a + color_b.cw * (1 - weight_a))
        - sign(color_b.cw - color_a.cw, use_sign),
    )


def interpolate_points(p1: Point, p2: Point, num: int, index: int) -> Point:
    """Get the center of one of ``num`` equal parts of a line.

    Args:
        p1: The start of the line.
        p2: The end of the line.
        num: The number of parts.
        index: The index of the part, from 0 to ``num - 1``.

    Returns:
        The center point of the part.
    """
    return (p1 - p2) / num * (index + 0.5) + p1


def to_hex(color: RGBCCT) -> str:
    """Format the RGB channels of a color as an HTML hex color.

    Args:
        color: The color. The white channels are ignored.

    Returns:
        The color as ``#rrggbb``.
    """
    return f"#{color.r:02x}{color.g:02x}{color.b:02x}"


def render(
    animation: AnimationOrColor,
    time: float,
    ctx: SceneContext,
    led: LED,
    objects: Sequence[TrackedPoint],
) -> RGBCCT:
    """Get the color of one LED from an animation or a static color.

    Args:
        animation: The animation, or a static color.
        time: The animation time in seconds.
        ctx: The scene context.
        led: The LED.
        objects: The detected persons.

    Returns:
        The color of the LED.
    """
    if isinstance(animation, RGBCCT):
        return animation
    return animation(time, ctx, led, objects)


def as_animation(value: object) -> AnimationOrColor:
    """Make sure that a parsed config value can drive the LEDs.

    Args:
        value: The result of `parse_animation`.

    Returns:
        The same value, with the animation type.

    Raises:
        TypeError: If the value is not a color and not callable.
    """
    if isinstance(value, RGBCCT):
        return value
    if callable(value):
        # The registry holds only animation factories, so a callable result
        # is an animation. Python cannot check the signature at run time.
        return cast("Animation", value)
    msg = f"The animation config gives {value!r}, not an animation or a color"
    raise TypeError(msg)


def _is_color(config: Mapping[str, YamlValue]) -> TypeGuard[ColorConfig]:
    return "r" in config and "g" in config and "b" in config


def _mapping_args(
    sig: inspect.Signature,
    anim_name: str,
    anim_args: Mapping[str, YamlValue],
    parse: Callable[[YamlValue], object],
) -> tuple[list[object], dict[str, object]]:
    valid_param_names = {p.name for p in sig.parameters.values()}
    for arg_name in anim_args:
        if arg_name not in valid_param_names:
            msg = f"Unknown parameter '{arg_name}' for animation '{anim_name}'"
            raise ValueError(msg)

    var_args: list[object] = []
    parsed_args: dict[str, object] = {}
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            if param.name in anim_args:
                values = anim_args[param.name]
                if not isinstance(values, list):
                    msg = (
                        f"Parameter '{param.name}' of animation "
                        f"'{anim_name}' must be a list"
                    )
                    raise TypeError(msg)
                var_args.extend(parse(arg) for arg in values)
            continue

        if param.name in anim_args:
            arg_value = anim_args[param.name]
            if isinstance(arg_value, list):
                parsed_args[param.name] = [parse(v) for v in arg_value]
            else:
                parsed_args[param.name] = parse(arg_value)
        elif param.default is not inspect.Parameter.empty:
            parsed_args[param.name] = param.default
    return var_args, parsed_args


def _scalar_args(sig: inspect.Signature, anim_arg: YamlValue) -> dict[str, object]:
    parsed_args: dict[str, object] = {}
    params = [
        p
        for p in sig.parameters.values()
        if p.name != "visited_presets"
        and p.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    ]
    if params:
        parsed_args[params[0].name] = anim_arg

    for param in sig.parameters.values():
        if (
            param.name not in parsed_args
            and param.default is not inspect.Parameter.empty
        ):
            parsed_args[param.name] = param.default
    return parsed_args


def parse_animation(
    anim_config: YamlValue,
    animation_functions: Mapping[str, AnimationFactory],
    visited_presets: set[str] | None = None,
) -> object:
    """Build an animation from its config.

    A mapping with the keys ``r``, ``g`` and ``b`` is a color. A different
    mapping has one key, the name of a function in ``animation_functions``.
    Its value holds the arguments of the function. A mapping gives keyword
    arguments. A different value is the first positional argument. The
    function parses nested configs recursively.

    Args:
        anim_config: The config value.
        animation_functions: The functions that the config can call, by name.
        visited_presets: The names of the presets that enclose this config.
            The ``preset`` function uses them to stop recursive presets.

    Returns:
        The animation, the color, or ``anim_config`` itself if it is not a
        mapping.

    Raises:
        ValueError: If the config names an unknown function or parameter.
        TypeError: If the value of a variadic parameter is not a list.
    """
    if not isinstance(anim_config, dict):
        return anim_config

    if _is_color(anim_config):
        return RGBCCT(**anim_config)

    items = list(anim_config.items())
    anim_name, anim_args = items[0]

    anim_func = animation_functions.get(anim_name)
    if not anim_func:
        msg = f"Unknown animation function: {anim_name}"
        raise ValueError(msg)

    sig = inspect.signature(anim_func)

    def parse(value: YamlValue) -> object:
        return parse_animation(value, animation_functions, visited_presets)

    if isinstance(anim_args, dict):
        var_args, parsed_args = _mapping_args(sig, anim_name, anim_args, parse)
    else:
        var_args, parsed_args = [], _scalar_args(sig, anim_args)

    if "visited_presets" in sig.parameters:
        parsed_args["visited_presets"] = visited_presets

    return anim_func(*var_args, **parsed_args)
