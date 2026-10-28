"""Load the installation config and build the LED layout from it."""

import os
import threading
from pathlib import Path
from typing import TypedDict

import yaml
from rpi_ws2805 import RGBCCT

from .animations import idle, meta, responsive
from .helpers import AnimationFactory, as_animation, interpolate_points, parse_animation
from .types import LED, AnimationOrColor, Point, Rectangle, Strip, YamlValue
from .yaml_loader import GangwayLoader


class ProjectionConfig(TypedDict, total=False):
    """The ``projection`` section of the config file.

    Attributes:
        src_points: Four reference points in the camera image.
        dst_points: The floor positions of the reference points.
        cutout: Four camera image points that frame the live view.
        floor: The floor area as ``[x1, y1, x2, y2]``.
    """

    src_points: list[list[float]]
    dst_points: list[list[float]]
    cutout: list[list[float]]
    floor: list[float]


class LedsConfig(TypedDict, total=False):
    """The ``leds`` section of the config file.

    Attributes:
        target_weight: The weight of the target color for each frame.
        offset_x: The x offset for all strips.
        offset_y: The y offset for all strips.
    """

    target_weight: float
    offset_x: float
    offset_y: float


class StripConfig(TypedDict):
    """One item of the ``strips`` section of the config file.

    Attributes:
        index: The index of the first LED in the LED chain.
        len: The number of LEDs.
        start: The floor position of the start as ``[x, y]``.
        end: The floor position of the end as ``[x, y]``.
    """

    index: int
    len: int
    start: list[float]
    end: list[float]


class ConfigFile(TypedDict, total=False):
    """The structure of the config file.

    Attributes:
        projection: The camera to floor projection.
        leds: The global LED settings.
        strips: The LED strip segments.
        animation: The config of the active animation.
    """

    projection: ProjectionConfig
    leds: LedsConfig
    strips: list[StripConfig]
    animation: YamlValue


def _get_animation_functions() -> dict[str, AnimationFactory]:
    functions: dict[str, AnimationFactory] = {}
    for package in (idle, responsive, meta):
        for name in package.__all__:
            functions[name] = getattr(package, name)
    functions["RGBCCT"] = RGBCCT
    return functions


ANIMATION_FUNCTIONS = _get_animation_functions()
"""The functions that the animation config can call, by name."""


class GANGWAYConfig:
    """The installation config, loaded from a YAML file.

    Attributes:
        path: The path of the config file.
        data: The raw content of the config file.
        SRC_POINTS: Four reference points in the camera image.
        DST_POINTS: The floor positions of the reference points.
        CUTOUT: Four camera image points that frame the live view.
        FLOOR: The floor area.
        TARGET_WEIGHT: The weight of the target color for each frame.
        STRIPS: The LED strip segments, with the offset applied.
        OFFSET_X: The x offset for all strips.
        OFFSET_Y: The y offset for all strips.
        LEDS: All LEDs with their floor positions.
        ANIMATION: The active animation.
    """

    path: Path
    data: ConfigFile
    SRC_POINTS: list[tuple[float, ...]]
    DST_POINTS: list[tuple[float, ...]]
    CUTOUT: list[tuple[float, ...]]
    FLOOR: Rectangle
    TARGET_WEIGHT: float
    STRIPS: list[Strip]
    OFFSET_X: float
    OFFSET_Y: float
    LEDS: list[LED]
    ANIMATION: AnimationOrColor

    def __init__(self, path: Path, *, load: bool = True) -> None:
        """Load the config file.

        Args:
            path: The path of the config file.
            load: Whether to read the file now. If false, call `load` later.
        """
        self._lock = threading.Lock()
        self.path = path
        if load:
            self.load()

    def load(self) -> None:
        """Read the config file again and update all attributes.

        Raises:
            ValueError: If the animation config is not valid.
            TypeError: If the animation config is not valid.
        """
        with self._lock:
            with open(self.path) as f:
                config: ConfigFile = yaml.load(f, Loader=GangwayLoader)

            self.data = config
            projection = config.get("projection", {})
            self.SRC_POINTS = [tuple(p) for p in projection.get("src_points", [])]
            self.DST_POINTS = [tuple(p) for p in projection.get("dst_points", [])]
            self.CUTOUT = [tuple(p) for p in projection.get("cutout", [])]

            floor_rect = tuple(projection.get("floor", (0, 0, 0, 0)))

            self.FLOOR = Rectangle(
                Point.from_tuple(floor_rect[:2]),
                Point.from_tuple(floor_rect[2:]),
            )

            leds_config = config.get("leds", {})
            self.TARGET_WEIGHT = leds_config.get("target_weight", 0.1)
            self.OFFSET_X = leds_config.get("offset_x", 0)
            self.OFFSET_Y = leds_config.get("offset_y", 0)

            offset = Point(x=self.OFFSET_X, y=self.OFFSET_Y)
            self.STRIPS = [
                Strip(
                    index=s.get("index"),
                    len=s.get("len"),
                    start=Point(*s.get("start")) + offset,
                    end=Point(*s.get("end")) + offset,
                )
                for s in config.get("strips", [])
            ]

            self.LEDS = [
                LED(
                    i + strip.index,
                    interpolate_points(strip.start, strip.end, strip.len, i),
                    strip_idx,
                )
                for strip_idx, strip in enumerate(self.STRIPS)
                for i in range(strip.len)
            ]

            self.ANIMATION = as_animation(
                parse_animation(config.get("animation", {}), ANIMATION_FUNCTIONS)
            )

    def save(self) -> None:
        """Write the config file again with its current content.

        The application does not change the config at run time, so this
        writes back what is in the file.
        """
        with self._lock:
            with open(self.path) as f:
                config: ConfigFile = yaml.load(f, Loader=GangwayLoader)

            with open(self.path, "w") as f:
                yaml.dump(config, f)


# GANGWAY_CONFIG names a config file outside the source tree. The presets
# directory is next to it, and the modules that read presets resolve that path
# at import time, so --config is too late for them.
CONFIG = GANGWAYConfig(
    Path(
        os.environ.get("GANGWAY_CONFIG", Path(__file__).parent.parent / "config.yaml")
    ),
    load=False,
)
"""The global config instance."""

# A `preset` animation reads CONFIG.path while the file loads, so the name
# must be bound before the first load.
CONFIG.load()
