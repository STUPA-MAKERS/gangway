"""API endpoints for animation presets.

A preset is a YAML file in the presets directory. The file holds one
animation config. The presets directory is next to the config file.
"""

import contextlib
import re

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import CONFIG, ConfigFile
from ..state import STATE
from ..types import YamlValue
from ..yaml_loader import GangwayLoader
from .models import AnimationModel

router = APIRouter()

PRESETS_DIR = CONFIG.path.parent / "presets"
"""The directory of the preset files."""
PRESETS_DIR.mkdir(exist_ok=True)


def validate_preset_name(name: str) -> None:
    """Make sure that a preset name is safe as a file name.

    Args:
        name: The preset name.

    Raises:
        HTTPException: 400 if the name has characters other than letters,
            digits, spaces, hyphens and underscores.
    """
    if not re.match(r"^[a-zA-Z0-9 \-_]+$", name):
        raise HTTPException(
            status_code=400,
            detail=(
                "Preset name must only contain alphanumeric characters, spaces, "
                "hyphens, and underscores."
            ),
        )


def find_preset_usage(data: YamlValue, target_name: str) -> bool:
    """Find a reference to a preset in an animation config.

    Args:
        data: The animation config.
        target_name: The preset name.

    Returns:
        True if the config uses the preset.
    """
    if isinstance(data, dict):
        if "preset" in data:
            val = data["preset"]
            if val == target_name:
                return True
            if isinstance(val, dict) and val.get("name") == target_name:
                return True

        return any(find_preset_usage(value, target_name) for value in data.values())

    if isinstance(data, list):
        return any(find_preset_usage(item, target_name) for item in data)

    return False


def update_preset_references(data: YamlValue, old_name: str, new_name: str) -> bool:
    """Rename the preset references in an animation config in place.

    Args:
        data: The animation config. The function changes it.
        old_name: The old preset name.
        new_name: The new preset name.

    Returns:
        True if the function changed one or more references.
    """
    updated = False
    if isinstance(data, dict):
        if "preset" in data:
            val = data["preset"]
            if val == old_name:
                data["preset"] = new_name
                updated = True
            elif isinstance(val, dict) and val.get("name") == old_name:
                val["name"] = new_name
                updated = True

        for value in data.values():
            if update_preset_references(value, old_name, new_name):
                updated = True

    elif isinstance(data, list):
        for item in data:
            if update_preset_references(item, old_name, new_name):
                updated = True

    return updated


def _reload() -> None:
    CONFIG.load()
    if STATE.led_controller:
        STATE.led_controller.reload_config()


class PresetModel(BaseModel):
    """A preset with its name and animation."""

    name: str
    animation: AnimationModel


@router.get("/", response_model=list[str])
def list_presets() -> list[str]:
    """List the names of all presets.

    Returns:
        The preset names.
    """
    return [p.stem for p in PRESETS_DIR.glob("*.yaml")]


@router.get("/{name}", response_model=PresetModel)
def get_preset(name: str) -> PresetModel:
    """Get the animation of a preset.

    Args:
        name: The preset name.

    Returns:
        The preset.

    Raises:
        HTTPException: 404 if the preset does not exist, 500 if it is not
            valid.
    """
    preset_path = PRESETS_DIR / f"{name}.yaml"
    if not preset_path.exists():
        raise HTTPException(status_code=404, detail="Preset not found")

    try:
        with open(preset_path) as f:
            animation_data = yaml.load(f, Loader=GangwayLoader)
        return PresetModel(name=name, animation=animation_data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load preset: {e}"
        ) from e


@router.post("/{name}")
def save_preset(name: str, animation: AnimationModel | None = None) -> dict[str, str]:
    """Save a preset.

    Args:
        name: The preset name.
        animation: The animation to save. If the request has no body, the
            function saves the active animation from the config file.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 400 if the name is not valid, 500 if the preset
            cannot be saved.
    """
    validate_preset_name(name)

    animation_data: YamlValue
    if animation is None:
        try:
            with open(CONFIG.path) as f:
                current_config: ConfigFile = yaml.load(f, Loader=GangwayLoader)
                animation_data = current_config.get("animation")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read current config: {e}"
            ) from e
    else:
        animation_data = animation.model_dump()

    preset_path = PRESETS_DIR / f"{name}.yaml"
    try:
        with open(preset_path, "w") as f:
            yaml.dump(animation_data, f, sort_keys=False)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save preset: {e}"
        ) from e

    _reload()

    return {"message": f"Preset '{name}' saved"}


@router.post("/{name}/load")
def load_preset(name: str) -> dict[str, str]:
    """Make a preset the active animation.

    Args:
        name: The preset name.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 404 if the preset does not exist, 500 if it cannot be
            applied.
    """
    preset_path = PRESETS_DIR / f"{name}.yaml"
    if not preset_path.exists():
        raise HTTPException(status_code=404, detail="Preset not found")

    try:
        with open(preset_path) as f:
            animation_data: YamlValue = yaml.load(f, Loader=GangwayLoader)

        with open(CONFIG.path) as f:
            config_data: ConfigFile = yaml.load(f, Loader=GangwayLoader)

        config_data["animation"] = animation_data

        with open(CONFIG.path, "w") as f:
            yaml.dump(config_data, f, sort_keys=False)

        _reload()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load/apply preset: {e}"
        ) from e
    return {"message": f"Preset '{name}' loaded"}


@router.post("/{name}/rename")
def rename_preset(name: str, new_name: str) -> dict[str, str]:
    """Rename a preset and update all references to it.

    Args:
        name: The old preset name.
        new_name: The new preset name.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 400 if the new name is not valid or exists, 404 if
            the preset does not exist, 500 if the rename fails.
    """
    validate_preset_name(new_name)

    old_path = PRESETS_DIR / f"{name}.yaml"
    new_path = PRESETS_DIR / f"{new_name}.yaml"

    if not old_path.exists():
        raise HTTPException(status_code=404, detail="Preset not found")

    if new_path.exists():
        raise HTTPException(
            status_code=400, detail=f"Preset '{new_name}' already exists"
        )

    try:
        old_path.rename(new_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to rename preset file: {e}"
        ) from e

    try:
        with open(CONFIG.path) as f:
            config_data: ConfigFile = yaml.load(f, Loader=GangwayLoader)

        if update_preset_references(config_data.get("animation"), name, new_name):
            with open(CONFIG.path, "w") as f:
                yaml.dump(config_data, f, sort_keys=False)

            _reload()

    except Exception as e:
        with contextlib.suppress(Exception):
            new_path.rename(old_path)
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update active config references (changes rolled back): {e}"
            ),
        ) from e

    # This also updates the renamed preset if it refers to itself.
    for p in PRESETS_DIR.glob("*.yaml"):
        try:
            with open(p) as f:
                content: YamlValue = yaml.load(f, Loader=GangwayLoader)

            if update_preset_references(content, name, new_name):
                with open(p, "w") as f:
                    yaml.dump(content, f, sort_keys=False)
        except Exception as e:
            # The rename itself is done. A broken reference in a different
            # preset must not fail the request.
            print(f"Failed to update references in preset '{p.stem}': {e}")

    return {"message": f"Preset '{name}' renamed to '{new_name}'"}


@router.delete("/{name}")
def delete_preset(name: str) -> dict[str, str]:
    """Delete a preset that nothing uses.

    Args:
        name: The preset name.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 400 if the active config or a different preset uses
            the preset, 404 if it does not exist, 500 if the delete fails.
    """
    if find_preset_usage(CONFIG.data.get("animation"), name):
        raise HTTPException(
            status_code=400,
            detail=f"Preset '{name}' is currently in use in the active configuration.",
        )

    for p in PRESETS_DIR.glob("*.yaml"):
        if p.stem == name:
            continue

        try:
            with open(p) as f:
                content: YamlValue = yaml.load(f, Loader=GangwayLoader)
            if find_preset_usage(content, name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Preset '{name}' is used by another preset '{p.stem}'.",
                )
        except HTTPException:
            raise
        except Exception:
            # Skip a preset file that cannot be read. It cannot use the preset.
            continue

    preset_path = PRESETS_DIR / f"{name}.yaml"
    if not preset_path.exists():
        raise HTTPException(status_code=404, detail="Preset not found")
    try:
        preset_path.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete preset: {e}"
        ) from e
    return {"message": f"Preset '{name}' deleted"}
