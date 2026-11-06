"""Tests for the config API."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient
from rpi_ws2805 import RGBCCT

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
    """A request with no API key gets 403.

    §NF/security/access/000094
    """
    assert client.get("/api/config/").status_code == 403


def test_auth_invalid_key(client: TestClient) -> None:
    """A request with a wrong API key gets 403.

    §NF/security/access/000094
    """
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
    """The API saves the new animation and reloads the controller.

    §F/configuration/config-api/000059
    §F/lighting/render/000043
    """
    response = client.put(
        "/api/config/", json={**CONFIG_DATA, "animation": animation}, headers=HEADERS
    )

    assert response.status_code == 200, response.text
    saved = yaml.safe_load(CONFIG.path.read_text())
    assert next(iter(saved["animation"])) == next(iter(animation))
    controller.reload_config.assert_called_once()


AUDIO_ANIMATIONS: list[dict[str, object]] = [
    {
        "beat_wave": {
            "color": {"r": 255, "g": 255, "b": 255},
            "background": {"rainbow": {}},
            "direction": "x",
            "reverse": True,
            "speed": 300,
            "width": 50,
        }
    },
    {"beat_ripples": {"max_radius": 200}},
    {"spectrum": {"colors": [{"r": 255}, {"b": 255}], "min_brightness": 0.1}},
    {"beat_pulse": {"decay": 0.2}},
    {"level": {"source": "bass", "direction": "y"}},
    {"audio_gain": {"animation": {"rainbow": {}}, "source": "treble"}},
    {"beat_switch": {"animations": [{"beat_pulse": {}}], "beats_per_switch": 8}},
]


@pytest.mark.parametrize("animation", AUDIO_ANIMATIONS)
def test_update_config_with_audio_animations(
    client: TestClient, controller: MagicMock, animation: dict[str, object]
) -> None:
    """The API accepts each audio animation and the config loads it."""
    response = client.put(
        "/api/config/", json={**CONFIG_DATA, "animation": animation}, headers=HEADERS
    )

    assert response.status_code == 200, response.text
    assert not isinstance(CONFIG.ANIMATION, RGBCCT)
    controller.reload_config.assert_called_once()


def test_update_config_rejects_a_bad_audio_parameter(client: TestClient) -> None:
    """A value out of range or an unknown source gives 422.

    §F/lighting/animation-config/000046
    """
    for animation in (
        {"beat_switch": {"beats_per_switch": 0}},
        {"level": {"source": "loudness"}},
    ):
        response = client.put(
            "/api/config/",
            json={**CONFIG_DATA, "animation": animation},
            headers=HEADERS,
        )
        assert response.status_code == 422


def test_update_config_keeps_the_audio_section(
    client: TestClient, controller: MagicMock
) -> None:
    """A new animation keeps the audio section of the file, and no section stays.

    §F/configuration/config-api/000059
    §F/configuration/config-api/000060
    """
    _ = client.put("/api/config/", json=CONFIG_DATA, headers=HEADERS)
    assert "audio" not in yaml.safe_load(CONFIG.path.read_text())

    data = {**CONFIG_DATA, "audio": {"device": "USB", "noise_floor": 0.02}}
    CONFIG.path.write_text(yaml.safe_dump(data))
    response = client.put("/api/config/", json=CONFIG_DATA, headers=HEADERS)

    assert response.status_code == 200, response.text
    saved = yaml.safe_load(CONFIG.path.read_text())
    assert saved["audio"]["device"] == "USB"
    assert CONFIG.AUDIO.noise_floor == 0.02
    assert controller.reload_config.call_count == 2


def test_animations_endpoint_lists_the_audio_animations(client: TestClient) -> None:
    """The editor gets the audio animations with their parameters.

    §F/web-ui/editor/000092
    """
    response = client.get("/api/animations/", headers=HEADERS)
    by_name = {a["name"]: a for a in response.json()}

    names = {next(iter(a)) for a in AUDIO_ANIMATIONS}
    assert names <= set(by_name)
    params = {p["name"]: p for p in by_name["level"]["params"]}
    assert params["source"]["type"]["name"] == "Literal"
    assert params["reverse"]["type"]["name"] == "bool"


def test_audio_data_without_capture(client: TestClient) -> None:
    """The audio endpoint gives silence when no microphone thread runs.

    §F/live/data/000086
    """
    response = client.get("/api/data/audio", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["capturing"] is False
    assert response.json()["since_beat"] is None


def test_api_without_a_server_key_gives_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no API_KEY on the server, a request gets 500, also with a key.

    §NF/security/access/000095
    """
    monkeypatch.delenv("API_KEY")

    assert client.get("/api/config/").status_code == 500
    assert client.get("/api/config/", headers={"X-API-Key": ""}).status_code == 500


def test_live_data_is_empty_before_the_controller_starts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Persons, LEDs and rates are empty while no controller runs.

    §F/live/data/000087
    """
    monkeypatch.setattr(STATE, "led_controller", None)

    assert client.get("/api/data/objects", headers=HEADERS).json() == []
    assert client.get("/api/data/leds", headers=HEADERS).json() == {}
    assert set(client.get("/api/data/fps", headers=HEADERS).json().values()) == {0}


def test_fps_gives_the_frame_times_in_milliseconds(
    client: TestClient, controller: MagicMock
) -> None:
    """The rates endpoint gives the frame times in ms with two decimals.

    §F/lighting/render/000044
    """
    controller.fps = 59.123456
    controller.tpf_min = 0.0123456
    controller.tpf_max = 0.05
    controller.tpf_avg = 0.016912

    data = client.get("/api/data/fps", headers=HEADERS).json()

    assert data["fps"] == 59.12
    assert data["tpf_min"] == 12.35
    assert data["tpf_max"] == 50.0
    assert data["tpf_avg"] == 16.91
