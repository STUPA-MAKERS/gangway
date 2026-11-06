"""Tests for the preset API."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from gangway.api import app, presets
from gangway.config import CONFIG
from gangway.led_controller import LEDController
from gangway.state import STATE

API_KEY = "test-secret-key"
HEADERS = {"X-API-Key": API_KEY}

RED = {"r": 255, "g": 0, "b": 0, "cw": 0, "ww": 0}
BLUE = {"r": 0, "g": 0, "b": 255, "cw": 0, "ww": 0}


def _config(animation: object) -> dict[str, object]:
    return {
        "projection": {
            "src_points": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "dst_points": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "floor": [0, 0, 10, 10],
            "cutout": [],
        },
        "leds": {"target_weight": 0.5, "offset_x": 0, "offset_y": 0},
        "strips": [{"index": 0, "len": 10, "start": [0, 0], "end": [0, 10]}],
        "animation": animation,
    }


class StateDir:
    """A temporary state folder with a config file and a presets folder."""

    def __init__(self, root: Path) -> None:
        """Make the folder.

        Args:
            root: The folder.
        """
        self.config = root / "config.yaml"
        self.presets = root / "presets"
        self.presets.mkdir()
        self.write_config({"static": {"color": RED}})

    def write_config(self, animation: object) -> None:
        """Write the config file with an animation and load it.

        Args:
            animation: The animation config.
        """
        self.config.write_text(yaml.safe_dump(_config(animation)))
        CONFIG.load()

    def animation(self) -> object:
        """Read the animation of the config file.

        Returns:
            The animation config.
        """
        return yaml.safe_load(self.config.read_text())["animation"]

    def write_preset(self, name: str, animation: object) -> None:
        """Write a preset file.

        Args:
            name: The preset name.
            animation: The animation config.
        """
        (self.presets / f"{name}.yaml").write_text(yaml.safe_dump(animation))

    def preset(self, name: str) -> object:
        """Read a preset file.

        Args:
            name: The preset name.

        Returns:
            The animation config.
        """
        return yaml.safe_load((self.presets / f"{name}.yaml").read_text())


@pytest.fixture
def state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[StateDir]:
    """Point the config and the preset API at a temporary state folder."""
    monkeypatch.setenv("API_KEY", API_KEY)
    monkeypatch.setattr(CONFIG, "path", tmp_path / "config.yaml")
    monkeypatch.setattr(presets, "PRESETS_DIR", tmp_path / "presets")
    monkeypatch.setattr(STATE, "led_controller", MagicMock(spec=LEDController))
    yield StateDir(tmp_path)
    # The tests load the temporary config into the global CONFIG. Load the
    # real config again so that later tests see it.
    monkeypatch.undo()
    CONFIG.load()


@pytest.fixture
def client(state: StateDir) -> TestClient:
    """Get an API client for the temporary state folder."""
    del state
    return TestClient(app)


def test_list_gives_the_preset_names(state: StateDir, client: TestClient) -> None:
    """The list has the name of each preset file.

    §F/presets/library/000052
    """
    state.write_preset("Red", {"static": {"color": RED}})
    state.write_preset("Blue Trails", {"static": {"color": BLUE}})

    response = client.get("/api/presets/", headers=HEADERS)

    assert sorted(response.json()) == ["Blue Trails", "Red"]


@pytest.mark.parametrize("name", ["a.b", "a;b", "x!", "ä"])
def test_save_refuses_an_unsafe_name(
    state: StateDir, client: TestClient, name: str
) -> None:
    """A name with other characters than letters, digits, space, - and _ gets 400.

    §F/presets/library/000053
    """
    response = client.post(
        f"/api/presets/{name}", json={"static": {"color": BLUE}}, headers=HEADERS
    )

    assert response.status_code == 400
    assert list(state.presets.iterdir()) == []


def test_rename_refuses_an_unsafe_name(state: StateDir, client: TestClient) -> None:
    """A rename to an unsafe name gets 400 and keeps the file.

    §F/presets/library/000053
    """
    state.write_preset("Red", {"static": {"color": RED}})

    response = client.post(
        "/api/presets/Red/rename", params={"new_name": "../Red"}, headers=HEADERS
    )

    assert response.status_code == 400
    assert (state.presets / "Red.yaml").exists()


def test_save_without_a_body_stores_the_active_animation(
    state: StateDir, client: TestClient
) -> None:
    """A save with no body copies the animation of the config file.

    §F/presets/library/000054
    """
    response = client.post("/api/presets/Current", headers=HEADERS)

    assert response.status_code == 200, response.text
    assert state.preset("Current") == {"static": {"color": RED}}


def test_save_with_a_body_stores_the_body(state: StateDir, client: TestClient) -> None:
    """A save with a body stores the animation of the body.

    §F/presets/library/000054
    """
    response = client.post(
        "/api/presets/Blue", json={"static": {"color": BLUE}}, headers=HEADERS
    )

    assert response.status_code == 200, response.text
    assert state.preset("Blue") == {"static": {"color": BLUE}}


def test_load_makes_the_preset_active(state: StateDir, client: TestClient) -> None:
    """A load writes the animation of the preset into the config and reloads.

    §F/presets/library/000055
    """
    state.write_preset("Blue", {"static": {"color": BLUE}})

    response = client.post("/api/presets/Blue/load", headers=HEADERS)

    assert response.status_code == 200, response.text
    assert state.animation() == {"static": {"color": BLUE}}
    controller = STATE.led_controller
    assert isinstance(controller, MagicMock)
    controller.reload_config.assert_called_once()


def test_load_of_a_missing_preset_gives_404(
    state: StateDir, client: TestClient
) -> None:
    """A load of a preset with no file gets 404 and keeps the config.

    §F/presets/library/000055
    """
    response = client.post("/api/presets/Missing/load", headers=HEADERS)

    assert response.status_code == 404
    assert state.animation() == {"static": {"color": RED}}


def test_rename_updates_every_reference(state: StateDir, client: TestClient) -> None:
    """A rename changes the references in the config and in the other presets.

    §F/presets/library/000056
    """
    state.write_preset("Old", {"static": {"color": BLUE}})
    state.write_preset("Uses Old", {"blend": {"animations": [{"preset": "Old"}]}})
    state.write_config({"preset": {"name": "Old"}})

    response = client.post(
        "/api/presets/Old/rename", params={"new_name": "New"}, headers=HEADERS
    )

    assert response.status_code == 200, response.text
    assert not (state.presets / "Old.yaml").exists()
    assert state.preset("New") == {"static": {"color": BLUE}}
    assert state.animation() == {"preset": {"name": "New"}}
    assert state.preset("Uses Old") == {"blend": {"animations": [{"preset": "New"}]}}


def test_rename_to_an_existing_name_gives_400(
    state: StateDir, client: TestClient
) -> None:
    """A rename to the name of a different preset gets 400 and changes nothing.

    §F/presets/library/000056
    """
    state.write_preset("Red", {"static": {"color": RED}})
    state.write_preset("Blue", {"static": {"color": BLUE}})

    response = client.post(
        "/api/presets/Red/rename", params={"new_name": "Blue"}, headers=HEADERS
    )

    assert response.status_code == 400
    assert state.preset("Red") == {"static": {"color": RED}}
    assert state.preset("Blue") == {"static": {"color": BLUE}}


def test_rename_of_a_missing_preset_gives_404(
    state: StateDir, client: TestClient
) -> None:
    """A rename of a preset with no file gets 404.

    §F/presets/library/000056
    """
    response = client.post(
        "/api/presets/Missing/rename", params={"new_name": "New"}, headers=HEADERS
    )

    assert response.status_code == 404
    assert not (state.presets / "New.yaml").exists()


def test_delete_refuses_a_preset_of_the_config(
    state: StateDir, client: TestClient
) -> None:
    """A preset that the active config uses stays.

    §F/presets/library/000058
    """
    state.write_preset("Blue", {"static": {"color": BLUE}})
    state.write_config({"preset": {"name": "Blue"}})

    response = client.delete("/api/presets/Blue", headers=HEADERS)

    assert response.status_code == 400
    assert (state.presets / "Blue.yaml").exists()


def test_delete_refuses_a_preset_of_a_different_preset(
    state: StateDir, client: TestClient
) -> None:
    """A preset that a different preset uses stays.

    §F/presets/library/000058
    """
    state.write_preset("Blue", {"static": {"color": BLUE}})
    state.write_preset("Uses Blue", {"preset": "Blue"})

    response = client.delete("/api/presets/Blue", headers=HEADERS)

    assert response.status_code == 400
    assert (state.presets / "Blue.yaml").exists()


def test_delete_removes_an_unused_preset(state: StateDir, client: TestClient) -> None:
    """A preset that nothing uses goes away, and a missing one gets 404.

    §F/presets/library/000058
    """
    state.write_preset("Blue", {"static": {"color": BLUE}})

    assert client.delete("/api/presets/Blue", headers=HEADERS).status_code == 200
    assert not (state.presets / "Blue.yaml").exists()
    assert client.delete("/api/presets/Blue", headers=HEADERS).status_code == 404
