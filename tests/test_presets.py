"""Tests for the preset animation."""

from pathlib import Path

import pytest
import yaml
from rpi_ws2805 import RGBCCT

from gangway.animations.meta import preset
from gangway.config import ANIMATION_FUNCTIONS, CONFIG, GANGWAYConfig
from gangway.helpers import as_animation, parse_animation
from gangway.types import LED, AudioState, Point, Rectangle, SceneContext
from gangway.yaml_loader import GangwayLoader

BLUE_PRESET_YAML = """
r: 0
g: 0
b: 255
cw: 0
ww: 0
"""


@pytest.fixture
def state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the config at a state directory outside the source tree."""
    monkeypatch.setattr(CONFIG, "path", tmp_path / "config.yaml")
    (tmp_path / "presets").mkdir()
    return tmp_path


def test_preset_reads_presets_next_to_config(state_dir: Path) -> None:
    """Load a preset from the presets folder next to the config file."""
    (state_dir / "presets" / "Blue.yaml").write_text(BLUE_PRESET_YAML)

    assert preset("Blue") == RGBCCT(b=255)


def test_missing_preset_turns_leds_off(state_dir: Path) -> None:
    """Turn the LEDs off for a preset that has no file."""
    assert not (state_dir / "presets" / "Missing.yaml").exists()

    assert preset("Missing") == RGBCCT()


def test_config_with_preset_animation_loads(state_dir: Path) -> None:
    """Load a config whose animation is a preset from the state directory."""
    (state_dir / "presets" / "Blue.yaml").write_text(BLUE_PRESET_YAML)
    config_path = state_dir / "config.yaml"
    config_path.write_text("strips: []\nanimation:\n  preset:\n    name: Blue\n")

    assert RGBCCT(b=255) == GANGWAYConfig(config_path).ANIMATION


@pytest.mark.parametrize(
    "path",
    sorted((Path(__file__).parent.parent / "presets").glob("*.yaml")),
    ids=lambda p: p.stem,
)
def test_shipped_preset_renders(path: Path) -> None:
    """Parse each preset that the package installs and render one LED."""
    with open(path) as f:
        data = yaml.load(f, Loader=GangwayLoader)
    animation = as_animation(parse_animation(data, ANIMATION_FUNCTIONS))
    floor = Rectangle(Point(0, 0), Point(115, 505))
    ctx = SceneContext(floor=floor, leds=[], audio=AudioState(beats=(0.5,)))

    color = (
        animation(1.0, ctx, LED(index=0, p=Point(50, 200)), [])
        if callable(animation)
        else animation
    )

    assert isinstance(color, RGBCCT)
