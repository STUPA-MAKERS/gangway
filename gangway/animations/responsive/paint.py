"""The `paint` animation."""

from collections.abc import Sequence

from rpi_ws2805 import RGBCCT

from ...types import LED, Animation, AnimationOrColor, SceneContext, TrackedPoint


def paint(
    primary: AnimationOrColor = RGBCCT(r=255, g=0, b=0),
    secondary: AnimationOrColor = RGBCCT(r=0, g=0, b=0),
    radius: float = 150,
    persistence: float = 2.0,
) -> Animation:
    """Show ``primary`` around each person and along their recent path.

    This is like `dot`, but each position stays lit for ``persistence``
    seconds.

    Args:
        primary: The animation on the path.
        secondary: The animation outside the path.
        radius: The radius around each position.
        persistence: The time that a position stays lit in seconds.

    Returns:
        The animation.
    """
    history: list[tuple[float, float, float]] = []
    last_frame_time = -1.0
    last_sample_time = -1.0
    active_points: list[tuple[float, float]] = []

    # A sample rate of 20 Hz keeps the history short enough to check for
    # each LED in each frame.
    sample_rate = 0.05
    radius_sq = radius**2

    def animation(
        time: float,
        ctx: SceneContext,
        led: LED,
        objects: Sequence[TrackedPoint],
    ) -> RGBCCT:
        nonlocal history, last_frame_time, last_sample_time, active_points

        # The function runs once for each LED, but the time only changes
        # between frames. Update the history only on the first call of a frame.
        if time > last_frame_time:
            cutoff = time - persistence
            history = [h for h in history if h[2] > cutoff]

            if time - last_sample_time >= sample_rate:
                history.extend((obj.x, obj.y, time) for obj in objects)
                last_sample_time = time

            active_points = [(x, y) for x, y, _ in history]
            # The current positions are not always in the history, because
            # of the sample rate. Add them so that a new person shows at once.
            active_points.extend((obj.x, obj.y) for obj in objects)

            last_frame_time = time

        primary_rgbcct = (
            primary if isinstance(primary, RGBCCT) else primary(time, ctx, led, objects)
        )
        secondary_rgbcct = (
            secondary
            if isinstance(secondary, RGBCCT)
            else secondary(time, ctx, led, objects)
        )

        led_x = led.p.x
        led_y = led.p.y
        hit = False
        for px, py in active_points:
            # Squared distances save a square root for each point.
            dist_sq = (led_x - px) ** 2 + (led_y - py) ** 2
            if dist_sq < radius_sq:
                hit = True
                break

        return primary_rgbcct if hit else secondary_rgbcct

    return animation
