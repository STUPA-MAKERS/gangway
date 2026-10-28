#!/usr/bin/env python3
"""
Definitions for LED positions
"""

import inspect
import os
import threading
from pathlib import Path
from typing import List, Tuple

import yaml
from rpi_ws2805 import RGBCCT

from .animations import idle, meta, responsive
from .helpers import interpolate_points, parse_animation
from .types import LED, Animation, Point, Rectangle, Strip


def _get_animation_functions():
    """Dynamically collects all animation functions from imported modules."""
    functions = {}
    # Inspect idle and object animation modules
    for module in [idle, responsive, meta]:
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Add function to registry if it's not a private helper
            if not name.startswith("_") and name != "interpolate_rgbcct":
                functions[name] = func
    # Add the color class for type checking
    functions["RGBCCT"] = RGBCCT
    return functions


ANIMATION_FUNCTIONS = _get_animation_functions()


class GANGWAYConfig:
    SRC_POINTS: List[Tuple[int, int]]
    DST_POINTS: List[Tuple[int, int]]
    CUTOUT: List[Tuple[float, float]]
    FLOOR: Rectangle
    TARGET_WEIGHT: float
    STRIPS: List[Strip]
    OFFSET_X: int
    OFFSET_Y: int
    LEDS: List[LED]
    ANIMATION: Animation | RGBCCT
    MQTT_HOST: str
    MQTT_PORT: int
    MQTT_USERNAME: str | None
    MQTT_PASSWORD: str | None
    MQTT_TOPIC_PREFIX: str

    def __init__(self, path: Path):
        self._lock = threading.Lock()
        self.path = path
        self.load()

    def load(self):
        with self._lock:
            with open(self.path, "r") as f:
                config = yaml.safe_load(f)

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

            self.STRIPS = [
                Strip(
                    index=s.get("index"),
                    len=s.get("len"),
                    start=Point(*s.get("start"))
                    + Point(x=self.OFFSET_X, y=self.OFFSET_Y),
                    end=Point(*s.get("end")) + Point(x=self.OFFSET_X, y=self.OFFSET_Y),
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

            self.ANIMATION = parse_animation(
                config.get("animation", {}), ANIMATION_FUNCTIONS
            )

            mqtt_config = config.get("mqtt", {})
            self.MQTT_HOST = mqtt_config.get("host", "localhost")
            self.MQTT_PORT = mqtt_config.get("port", 1883)
            self.MQTT_USERNAME = mqtt_config.get("username")
            self.MQTT_PASSWORD = mqtt_config.get("password")
            self.MQTT_TOPIC_PREFIX = mqtt_config.get("topic_prefix", "gangway")

    def save(self):
        with self._lock:
            # This is a bit tricky as we have complex objects.
            # We'll just save the raw dictionary for now.
            # A more robust solution would be to serialize the objects back to the YAML structure.
            with open(self.path, "r") as f:
                config = yaml.safe_load(f)

            # We are not modifying the config at runtime in this application, so we can just
            # save the file as is. If we were to modify the config, we would need to
            # reconstruct the dictionary from the class attributes.
            with open(self.path, "w") as f:
                yaml.dump(config, f)


# Global config instance. GANGWAY_CONFIG names a config file outside the source
# tree. The presets directory is next to it, and the modules that read presets
# resolve that path at import time, so --config is too late for them.
CONFIG = GANGWAYConfig(
    Path(os.environ.get("GANGWAY_CONFIG", Path(__file__).parent.parent / "config.yaml"))
)
