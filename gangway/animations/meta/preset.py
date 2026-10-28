"""The `preset` animation."""

import yaml
from rpi_ws2805 import RGBCCT

from ...helpers import as_animation, parse_animation
from ...types import (
    AnimationOrColor,
    YamlValue,
)


def preset(name: str, visited_presets: set[str] | None = None) -> AnimationOrColor:
    """Load the animation of a preset file.

    Args:
        name: The name of the preset.
        visited_presets: The names of the presets that enclose this one.

    Returns:
        The animation of the preset. A missing, empty or recursive preset
        turns all LEDs off.
    """
    # gangway.config imports this module, so import it at call time.
    from ...config import ANIMATION_FUNCTIONS, CONFIG  # noqa: PLC0415

    if visited_presets is None:
        visited_presets = set()

    if name in visited_presets:
        return RGBCCT()

    new_visited = visited_presets.copy()
    new_visited.add(name)

    # The API keeps the presets next to the config file. On the Pi
    # that is the state directory, not the read-only source tree.
    preset_path = CONFIG.path.parent / "presets" / f"{name}.yaml"

    if not preset_path.exists():
        return RGBCCT()

    with open(preset_path) as f:
        anim_config: YamlValue = yaml.safe_load(f)

    if anim_config is None:
        return RGBCCT()

    return as_animation(
        parse_animation(anim_config, ANIMATION_FUNCTIONS, visited_presets=new_visited)
    )
