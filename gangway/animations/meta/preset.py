"""The `preset` animation."""

from pathlib import Path

import yaml
from rpi_ws2805 import RGBCCT

from ...helpers import as_animation, parse_animation
from ...types import (
    AnimationOrColor,
    YamlValue,
)


def _read_preset(path: Path) -> YamlValue:
    """Read a preset file. A missing file gives None, like an empty one."""
    if not path.exists():
        return None
    with path.open() as f:
        content: YamlValue = yaml.safe_load(f)
    return content


def preset(name: str, visited_presets: set[str] | None = None) -> AnimationOrColor:
    """Load the animation of a preset file.

    The presets are in the ``presets`` folder next to the config file, like
    in the API. On the Pi that is the state directory, not the read-only
    source tree.

    Args:
        name: The name of the preset.
        visited_presets: The names of the presets that enclose this one.

    Returns:
        The animation of the preset. A missing, empty or recursive preset
        turns all LEDs off.
    """
    # gangway.config imports this module, so import it at call time.
    from ...config import ANIMATION_FUNCTIONS, CONFIG  # noqa: PLC0415

    visited = visited_presets or set[str]()
    if name in visited:
        return RGBCCT()

    anim_config = _read_preset(CONFIG.path.parent / "presets" / f"{name}.yaml")
    return (
        RGBCCT()
        if anim_config is None
        else as_animation(
            parse_animation(
                anim_config, ANIMATION_FUNCTIONS, visited_presets=visited | {name}
            )
        )
    )
