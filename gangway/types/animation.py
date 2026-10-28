"""The `Animation` and `AnimationOrColor` types."""

from collections.abc import Callable, Sequence

from rpi_ws2805 import RGBCCT

from .led import LED
from .scene_context import SceneContext
from .tracked_point import TrackedPoint

type Animation = Callable[[float, SceneContext, LED, Sequence[TrackedPoint]], RGBCCT]
"""Calculate the color of one LED for one frame.

The arguments are the time since the start in seconds, the scene context, the
LED, and the detected persons.
"""

type AnimationOrColor = Animation | RGBCCT
"""An animation, or a static color that is the same for all frames."""
