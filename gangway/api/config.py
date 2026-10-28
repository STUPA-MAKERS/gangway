"""API endpoints for the installation config."""

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import CONFIG
from ..state import STATE
from ..yaml_loader import GangwayLoader
from .models import AnimationModel

router = APIRouter()


class ProjectionModel(BaseModel):
    """The camera to floor projection."""

    src_points: list[list[float]]
    dst_points: list[list[float]]
    floor: list[float]
    cutout: list[list[float]] = []


class LedsModel(BaseModel):
    """The global LED settings."""

    target_weight: float
    offset_x: float
    offset_y: float


class StripModel(BaseModel):
    """One LED strip segment."""

    index: int
    len: int
    start: list[float]
    end: list[float]


class ConfigModel(BaseModel):
    """The config file content that the API shows and accepts."""

    projection: ProjectionModel
    leds: LedsModel
    strips: list[StripModel]
    animation: AnimationModel


@router.get("/", response_model=ConfigModel)
def get_config() -> ConfigModel:
    """Get the config from the config file.

    Returns:
        The config.

    Raises:
        HTTPException: 500 if the file cannot be read or is not valid.
    """
    try:
        with open(CONFIG.path) as f:
            raw_config = yaml.load(f, Loader=GangwayLoader)
        return ConfigModel(**raw_config)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load or validate config: {e}"
        ) from e


@router.put("/")
def update_config(new_config: ConfigModel) -> dict[str, str]:
    """Save a new animation to the config file and apply it.

    Only the animation changes. The function ignores the other sections of
    ``new_config``, so the API cannot change the hardware layout.

    Args:
        new_config: The new config.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 500 if the config cannot be saved or applied.
    """
    try:
        with open(CONFIG.path) as f:
            raw_config = yaml.load(f, Loader=GangwayLoader)
        old_config = ConfigModel(**raw_config)

        old_config.animation = new_config.animation

        config_dict = old_config.model_dump()

        with open(CONFIG.path, "w") as f:
            yaml.dump(config_dict, f, sort_keys=False)

        CONFIG.load()

        if STATE.led_controller:
            STATE.led_controller.reload_config()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update config: {e}"
        ) from e
    return {"message": "Config updated successfully"}
