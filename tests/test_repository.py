"""Tests for the files of the repository outside the application."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def _config_path(env: dict[str, str]) -> Path:
    result = subprocess.run(
        [sys.executable, "-c", "from gangway.config import CONFIG; print(CONFIG.path)"],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
        env=env,
    )
    return Path(result.stdout.strip())


def test_gangway_config_names_the_config_file(tmp_path: Path) -> None:
    """GANGWAY_CONFIG selects the file, and without it the repository file loads.

    §F/configuration/config-file/000061
    """
    config = tmp_path / "config.yaml"
    config.write_text(
        yaml.safe_dump({"strips": [], "animation": {"r": 1, "g": 2, "b": 3}})
    )
    env = {k: v for k, v in os.environ.items() if k != "GANGWAY_CONFIG"}

    assert _config_path({**env, "GANGWAY_CONFIG": str(config)}) == config
    assert _config_path(env) == ROOT / "config.yaml"


def test_ui_kit_input_has_the_commit_of_the_submodule() -> None:
    """The ui-kit flake input and the submodule name the same commit.

    §S/shared/git/000032
    """
    tree = subprocess.run(
        ["git", "ls-tree", "HEAD", "frontend/vendor/ui-kit"],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    if tree.returncode != 0 or not tree.stdout:
        pytest.skip("The tests do not run in a git checkout.")
    submodule = tree.stdout.split()[2]
    flake = (ROOT / "flake.nix").read_text()
    pinned = re.search(r"github:STUPA-MAKERS/ui-kit/([0-9a-f]{40})", flake)

    assert pinned is not None
    assert pinned.group(1) == submodule
