"""Tests for the config loader."""

from pathlib import Path

import pytest
import yaml
from rpi_ws2805 import RGBCCT

from gangway.audio import AudioSettings
from gangway.config import GANGWAYConfig

SAMPLE_CONFIG_YAML = """
projection:
  src_points: [[0, 0], [100, 0], [100, 100], [0, 100]]
  dst_points: [[0, 0], [10, 0], [10, 10], [0, 10]]
  cutout: [[1, 1], [9, 9]]
  floor: [0, 0, 10, 10]

leds:
  target_weight: 0.5
  offset_x: 10
  offset_y: 20

strips:
  - index: 0
    len: 5
    start: [0, 0]
    end: [0, 5]

animation:
  r: 255
  g: 0
  b: 0
  ww: 0
  cw: 0
"""


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """Write the sample config to a temporary file."""
    path = tmp_path / "config.yaml"
    path.write_text(SAMPLE_CONFIG_YAML)
    return path


def test_load_config(config_path: Path) -> None:
    """The loader reads all sections and applies the strip offset."""
    cfg = GANGWAYConfig(config_path)

    assert len(cfg.SRC_POINTS) == 4
    assert cfg.SRC_POINTS[0] == (0, 0)
    assert cfg.FLOOR.p1.x == 0
    assert cfg.FLOOR.p2.x == 10

    assert cfg.TARGET_WEIGHT == 0.5
    assert cfg.OFFSET_X == 10
    assert cfg.OFFSET_Y == 20

    assert len(cfg.STRIPS) == 1
    strip = cfg.STRIPS[0]
    assert strip.index == 0
    assert strip.len == 5
    assert (strip.start.x, strip.start.y) == (10, 20)

    assert len(cfg.LEDS) == 5
    assert cfg.LEDS[0].index == 0

    assert RGBCCT(r=255) == cfg.ANIMATION


def test_save_config(config_path: Path) -> None:
    """Save writes back the same content."""
    cfg = GANGWAYConfig(config_path)
    cfg.save()

    assert yaml.safe_load(config_path.read_text()) == yaml.safe_load(SAMPLE_CONFIG_YAML)


def test_audio_section(config_path: Path) -> None:
    """A missing audio section gives the defaults, and a section sets them."""
    assert AudioSettings() == GANGWAYConfig(config_path).AUDIO

    config_path.write_text(
        SAMPLE_CONFIG_YAML + "\naudio:\n  enabled: false\n  device: 2\n"
    )
    expected = AudioSettings(enabled=False, device=2)
    assert expected == GANGWAYConfig(config_path).AUDIO
