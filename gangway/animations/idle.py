"""Animations that do not need detected persons."""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from rpi_ws2805 import RGBCCT

from ..helpers import interpolate_rgbcct
from ..types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint
from .meta import alternate, blend


@dataclass(frozen=True)
class _Wave:
    direction: tuple[float, float]
    color: RGBCCT
    phase: float


def wave(
    colors: list[RGBCCT],
    n_waves: int = 3,
    speed: float = 50.0,
    wavelength: float = 200.0,
) -> Animation:
    """Add up plane waves that move in random directions.

    Args:
        colors: The colors to select from. Each wave gets a random color.
        n_waves: The number of waves.
        speed: The speed of the waves in floor units per second.
        wavelength: The wavelength in floor units.

    Returns:
        The animation.
    """
    waves: list[_Wave] = []
    for i in range(n_waves):
        angle = random.uniform(0, 2 * math.pi)
        direction = (math.cos(angle), math.sin(angle))
        color = random.choice(colors)
        waves.append(
            _Wave(direction=direction, color=color, phase=(i / n_waves) * 2 * math.pi)
        )

    k = 2 * math.pi / wavelength

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        r, g, b, cw, ww = 0.0, 0.0, 0.0, 0.0, 0.0

        for wave_params in waves:
            direction = wave_params.direction
            color = wave_params.color

            proj = led.p.x * direction[0] + led.p.y * direction[1]
            intensity = (
                1 + math.sin(k * proj - (k * speed * time) + wave_params.phase)
            ) / 2

            r += color.r * intensity
            g += color.g * intensity
            b += color.b * intensity
            cw += color.cw * intensity
            ww += color.ww * intensity

        return RGBCCT(
            r=min(255, int(r)),
            g=min(255, int(g)),
            b=min(255, int(b)),
            cw=min(255, int(cw)),
            ww=min(255, int(ww)),
        )

    return animation


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    if s == 0.0:
        return int(v * 255), int(v * 255), int(v * 255)
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)


def rainbow(speed: float = 0.1, spread: float = 3.0) -> Animation:
    """Move a rainbow gradient along the x axis.

    Args:
        speed: The hue change per second.
        spread: The number of rainbows across the floor.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        x_norm = (led.p.x - ctx.floor.p1.x) / (ctx.floor.p2.x - ctx.floor.p1.x)
        hue = (x_norm * spread + time * speed) % 1.0
        r, g, b = _hsv_to_rgb(hue, 1.0, 1.0)
        return RGBCCT(r=r, g=g, b=b)

    return animation


def fire(
    base_color: RGBCCT = RGBCCT(r=255, g=140, b=0),
    flicker_speed: float = 0.1,
    flicker_intensity: float = 0.5,
) -> Animation:
    """Flicker the brightness of a color at random, like a fire.

    Args:
        base_color: The color at full brightness.
        flicker_speed: The time between two brightness changes in seconds.
        flicker_intensity: The maximum brightness decrease, from 0 to 1.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        time_bucket = int(time / flicker_speed)
        seed = hash((led.p.x, time_bucket))
        rand_gen = random.Random(seed)
        brightness_factor = 1.0 - flicker_intensity * rand_gen.random()

        return RGBCCT(
            r=int(base_color.r * brightness_factor),
            g=int(base_color.g * brightness_factor),
            b=int(base_color.b * brightness_factor),
            cw=int(base_color.cw * brightness_factor),
            ww=int(base_color.ww * brightness_factor),
        )

    return animation


def theater_chase(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255),
    speed: float = 1.0,
    spacing: int = 4,
) -> Animation:
    """Move a pattern of lit LEDs along the LED chain.

    Args:
        color: The color of the lit LEDs.
        speed: The speed. A value of 1 gives 10 steps per second.
        spacing: The distance between two lit LEDs.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        time_offset = int(time * speed * 10)
        if (led.index - time_offset) % spacing == 0:
            return color
        return RGBCCT()

    return animation


_STROBO_COLORS = (
    RGBCCT(r=255, g=255, b=255, cw=255, ww=255),
    RGBCCT(),
    RGBCCT(r=255),
    RGBCCT(),
    RGBCCT(b=255),
)


def strobo(
    colors: Sequence[RGBCCT] = _STROBO_COLORS,
    frequency: int = 100,
) -> Animation:
    """Show a sequence of colors on all LEDs, one color for each step.

    Args:
        colors: The color sequence.
        frequency: The number of steps per second.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return colors[int(time * frequency) % len(colors)]

    return animation


def swing(
    color: RGBCCT = RGBCCT(r=255, g=255, b=255, cw=255),
    direction: Literal["x", "y"] = "y",
    wavelength: int = 50,
    speed: float = 10,
) -> Animation:
    """Move a band of light back and forth along an axis.

    Args:
        color: The color of the band.
        direction: The axis of the movement.
        wavelength: The distance that halves the brightness, in floor units.
        speed: The angular speed of the movement in radians per second.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        coordinate: float = led.p.x if direction == "x" else led.p.y
        floor_len: float = (
            ctx.floor.p2.x - ctx.floor.p1.x
            if direction == "x"
            else ctx.floor.p2.y - ctx.floor.p1.y
        )

        target_coordinate: float = (
            math.sin(time * speed) * floor_len / 2 + floor_len / 2
        )

        intensity = 2 ** (-abs(coordinate - target_coordinate) / wavelength)

        if intensity < 0.2:
            intensity = 0

        return interpolate_rgbcct(color, RGBCCT(), intensity, use_sign=False)

    return animation


def static(color: RGBCCT = RGBCCT(r=255, g=255, b=255)) -> Animation:
    """Show one color on all LEDs.

    Args:
        color: The color.

    Returns:
        The animation.
    """

    def animation(
        _time: float,
        _ctx: SceneContext,
        _led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        return color

    return animation


def idle(
    idle_animation: AnimationOrColor, active_animation: AnimationOrColor
) -> Animation:
    """Select an animation from the presence of persons.

    Args:
        idle_animation: The animation when nobody is present.
        active_animation: The animation when one or more persons are present.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        objects = list(objects)

        if len(objects) == 0:
            return (
                idle_animation
                if isinstance(idle_animation, RGBCCT)
                else idle_animation(time, ctx, led, objects)
            )
        return (
            active_animation
            if isinstance(active_animation, RGBCCT)
            else active_animation(time, ctx, led, objects)
        )

    return animation


def sparkle(density: float = 0.1, speed: float = 20.0) -> Animation:
    """Light random LEDs in random colors.

    Args:
        density: The part of the LEDs that are lit, from 0 to 1.
        speed: The number of changes per second.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        seed = hash((led.index, int(time * speed)))
        rng = random.Random(seed)
        if rng.random() < density:
            return RGBCCT(
                r=rng.randint(0, 255),
                g=rng.randint(0, 255),
                b=rng.randint(0, 255),
            )
        return RGBCCT()

    return animation


def plasma(speed: float = 0.5, scale: float = 0.05) -> Animation:
    """Show a plasma effect from a sum of sine waves.

    Args:
        speed: The speed of the effect.
        scale: The spatial frequency of the waves.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        t = time * speed
        v = 0.0
        v += math.sin((led.p.x * scale) + t)
        v += math.sin((led.p.y * scale) / 2.0 + t)
        v += math.sin((led.p.x * scale + led.p.y * scale) / 2.0 + t)
        cx = led.p.x + 0.5 * math.sin(t / 5.0)
        cy = led.p.y + 0.5 * math.cos(t / 3.0)
        v += math.sin(math.sqrt((cx * scale) ** 2 + (cy * scale) ** 2) + t)
        v /= 4.0

        hue = (t + v) % 1.0
        r, g, b = _hsv_to_rgb(hue, 1.0, 1.0)
        return RGBCCT(r=r, g=g, b=b)

    return animation


def rave() -> Animation:
    """Alternate between strobe, glitter rainbow, chase and sparkle effects.

    Returns:
        The animation.
    """
    strobe_anim = strobo(
        colors=[
            RGBCCT(r=255),
            RGBCCT(),
            RGBCCT(g=255),
            RGBCCT(),
            RGBCCT(b=255),
            RGBCCT(),
            RGBCCT(cw=255),
            RGBCCT(),
        ],
        frequency=75,
    )
    rainbow_anim = rainbow(speed=2.0, spread=2.0)
    sparkle_anim = sparkle(density=0.2, speed=30.0)
    chase_anim = theater_chase(color=RGBCCT(r=255, g=0, b=255), speed=4.0, spacing=5)

    return alternate(
        strobe_anim,
        blend(rainbow_anim, sparkle_anim),
        chase_anim,
        sparkle_anim,
        length=1.5,
    )


def linear_rainbow(
    direction: Literal["x", "y"] = "x", speed: float = 0.1, spread: float = 3.0
) -> Animation:
    """Move a rainbow gradient along the x or y axis.

    Args:
        direction: The axis of the gradient.
        speed: The hue change per second.
        spread: The number of rainbows across the floor.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        if direction == "x":
            pos = led.p.x
            min_p = ctx.floor.p1.x
            max_p = ctx.floor.p2.x
        else:
            pos = led.p.y
            min_p = ctx.floor.p1.y
            max_p = ctx.floor.p2.y

        length = max_p - min_p
        if length == 0:
            length = 1.0

        x_norm = (pos - min_p) / length
        hue = (x_norm * spread + time * speed) % 1.0
        r, g, b = _hsv_to_rgb(hue, 1.0, 1.0)
        return RGBCCT(r=r, g=g, b=b)

    return animation


def northern_lights(
    speed: float = 0.5,
    intensity: float = 0.8,
) -> Animation:
    """Show flowing curtains of green, teal and purple.

    Args:
        speed: The speed of the flow.
        intensity: The brightness, from 0 to 1.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        t = time * speed

        dx = ctx.floor.p2.x - ctx.floor.p1.x
        dy = ctx.floor.p2.y - ctx.floor.p1.y
        x_norm = (led.p.x - ctx.floor.p1.x) / (dx if dx != 0 else 1.0)
        y_norm = (led.p.y - ctx.floor.p1.y) / (dy if dy != 0 else 1.0)

        v1 = math.sin(x_norm * 2.0 + t)
        v2 = math.sin(y_norm * 1.5 - t * 0.7 + v1)
        v3 = math.sin((x_norm + y_norm) * 3.0 + t * 1.5)

        # Green is the main color. Red and blue only add purple tints.
        r = (math.sin(v1 + t) * 0.5 + 0.5) * 50
        g = (math.sin(v2 + t * 0.5) * 0.5 + 0.5) * 200
        b = (math.sin(v3 - t) * 0.5 + 0.5) * 150

        return RGBCCT(
            r=int(r * intensity),
            g=int(g * intensity),
            b=int(b * intensity),
        )

    return animation


def lightning_storm(
    frequency: float = 0.02,
    base_brightness: float = 0.00,
) -> Animation:
    """Show random bright flashes over a dim background, like lightning.

    Args:
        frequency: The probability of a flash in each 0.5 second period.
        base_brightness: The cold white background level, from 0 to 1.

    Returns:
        The animation.
    """

    def animation(
        time: float,
        _ctx: SceneContext,
        led: LED,
        _objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        flash_period = 0.5
        flash_time = time % flash_period
        flash_seed = int(time / flash_period)

        rng = random.Random(flash_seed)
        has_flash = rng.random() < frequency

        if has_flash and flash_time < 0.2:
            # A seed from the LED index gives each LED a different flicker.
            led_flicker = random.Random(flash_seed + led.index).random() * 0.4 + 0.6
            flash_intensity = (
                math.exp(-flash_time * 15)
                * led_flicker
                * (math.sin(time * 100) * 0.2 + 0.8)
            )
            val = int(255 * flash_intensity)
            return RGBCCT(r=val, g=val, b=val, cw=val, ww=val)

        base = int(255 * base_brightness)
        return RGBCCT(cw=base)

    return animation
