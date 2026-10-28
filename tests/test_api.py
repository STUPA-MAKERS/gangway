"""Tests for the config API."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from gangway.api import app
from gangway.config import CONFIG
from gangway.led_controller import LEDController
from gangway.state import STATE

API_KEY = "test-secret-key"
HEADERS = {"X-API-Key": API_KEY}

CONFIG_DATA = {
    "projection": {
        "src_points": [[0, 0], [10, 0], [10, 10], [0, 10]],
        "dst_points": [[0, 0], [10, 0], [10, 10], [0, 10]],
        "floor": [0, 0, 10, 10],
        "cutout": [],
    },
    "leds": {"target_weight": 0.5, "offset_x": 0, "offset_y": 0},
    "strips": [{"index": 0, "len": 10, "start": [0, 0], "end": [0, 10]}],
    "animation": {"static": {"color": {"r": 255, "g": 0, "b": 0, "cw": 0, "ww": 0}}},
}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Get an API client for a temporary config file."""
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(CONFIG_DATA))
    monkeypatch.setenv("API_KEY", API_KEY)
    monkeypatch.setattr(CONFIG, "path", path)
    yield TestClient(app)
    # The update tests load the temporary config into the global CONFIG.
    # Load the real config again so that later tests see it.
    monkeypatch.undo()
    CONFIG.load()


@pytest.fixture
def controller(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the LED controller with a mock."""
    mock = MagicMock(spec=LEDController)
    monkeypatch.setattr(STATE, "led_controller", mock)
    return mock


def test_auth_missing_key(client: TestClient) -> None:
    """A request with no API key gets 403."""
    assert client.get("/api/config/").status_code == 403


def test_auth_invalid_key(client: TestClient) -> None:
    """A request with a wrong API key gets 403."""
    response = client.get("/api/config/", headers={"X-API-Key": "wrong"})
    assert response.status_code == 403


def test_get_config(client: TestClient) -> None:
    """The API returns the config file content."""
    response = client.get("/api/config/", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["leds"]["target_weight"] == 0.5


@pytest.mark.parametrize(
    "animation",
    [
        {"static": {"color": {"r": 0, "g": 255, "b": 0, "cw": 0, "ww": 0}}},
        {
            "by_strip": {
                "assignments": [
                    {
                        "strip_assignment": {
                            "strip": 1,
                            "animation": {
                                "static": {
                                    "color": {
                                        "r": 255,
                                        "g": 0,
                                        "b": 0,
                                        "cw": 0,
                                        "ww": 0,
                                    }
                                }
                            },
                        }
                    }
                ],
                "default": {
                    "static": {"color": {"r": 0, "g": 255, "b": 0, "cw": 0, "ww": 0}}
                },
            }
        },
    ],
)
def test_update_config(
    client: TestClient, controller: MagicMock, animation: dict[str, object]
) -> None:
    """The API saves the new animation and reloads the controller."""
    response = client.put(
        "/api/config/", json={**CONFIG_DATA, "animation": animation}, headers=HEADERS
    )

    assert response.status_code == 200, response.text
    saved = yaml.safe_load(CONFIG.path.read_text())
    assert next(iter(saved["animation"])) == next(iter(animation))
    controller.reload_config.assert_called_once()
