"""Tests for the preset animation."""

from pathlib import Path

import pytest
from rpi_ws2805 import RGBCCT

from gangway.animations.meta import preset
from gangway.config import CONFIG

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
