"""API endpoint that describes the available animations.

The endpoint reads the Pydantic models in `gangway.api.models`. These models
are the single source of truth for the animation structure. The frontend
builds its editor from the result.
"""

import inspect
from typing import ForwardRef, NotRequired, TypedDict, get_args, get_origin

from fastapi import APIRouter
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from .models import (
    AnimationModel,
    PresetParams,
    RGBCCTModel,
    StripAssignmentWrapper,
)

router = APIRouter()


class TypeInfo(TypedDict):
    """The description of a parameter type.

    Attributes:
        name: The type name, for example ``float``, ``RGBCCT`` or ``Union``.
        args: The type arguments of a generic type.
        module: Set to ``any`` for a nested animation.
    """

    name: str
    args: NotRequired[list["TypeInfo"]]
    module: NotRequired[str]


class ParamInfo(TypedDict):
    """The description of an animation parameter.

    Attributes:
        name: The parameter name.
        type: The parameter type.
        default: The default value, or None if there is no default.
        kind: The `inspect.Parameter` kind. The value is always
            ``POSITIONAL_OR_KEYWORD``.
        min: The lower limit, or None.
        max: The upper limit, or None.
    """

    name: str
    type: TypeInfo
    default: object
    kind: int
    min: int | float | None
    max: int | float | None


class AnimationInfo(TypedDict):
    """The description of an animation.

    Attributes:
        name: The animation name in the config.
        title: The display name.
        description: The description text.
        params: The parameters.
    """

    name: str
    title: str
    description: str | None
    params: list[ParamInfo]


_NAMED_TYPES: tuple[tuple[object, str], ...] = (
    (int, "int"),
    (float, "float"),
    (bool, "bool"),
    (str, "str"),
    (RGBCCTModel, "RGBCCT"),
    (PresetParams, "Preset"),
    (StripAssignmentWrapper, "StripAssignment"),
)


def _get_type_info(annotation: object) -> TypeInfo:
    if isinstance(annotation, ForwardRef):
        return {"name": "Animation", "module": "any"}

    for known, name in _NAMED_TYPES:
        if annotation is known:
            return {"name": name}

    origin: object = get_origin(annotation)
    args: tuple[object, ...] = get_args(annotation)

    if origin:
        origin_name = str(getattr(origin, "__name__", str(origin)))

        if origin_name == "Literal":
            return {"name": "Literal", "args": [{"name": str(arg)} for arg in args]}

        # Optional[T] is Union[T, None]. The frontend does not show None.
        processed_args = [_get_type_info(arg) for arg in args if arg is not type(None)]
        return {"name": origin_name, "args": processed_args}

    return {"name": "any"}


def _get_limit(source: object, *names: str) -> int | float | None:
    for name in names:
        value: object = getattr(source, name, None)
        if isinstance(value, int | float):
            return value
    return None


def _as_limit(value: object) -> int | float | None:
    return value if isinstance(value, int | float) else None


def _get_params(params_model: type[BaseModel]) -> list[ParamInfo]:
    params_list: list[ParamInfo] = []
    for param_name, param_field in params_model.model_fields.items():
        default_val: object = param_field.get_default()

        if default_val is PydanticUndefined:
            serializable_default = None
        elif isinstance(default_val, BaseModel):
            serializable_default = default_val.model_dump()
        else:
            serializable_default = default_val

        # Use gt and lt as inclusive limits if ge and le are not set. The
        # limits are only a hint for the UI.
        min_val = _get_limit(param_field, "ge", "gt")
        max_val = _get_limit(param_field, "le", "lt")

        # Pydantic v2 keeps the limits in the field metadata.
        for meta in param_field.metadata:
            meta_min = _get_limit(meta, "ge", "gt")
            if meta_min is not None:
                min_val = meta_min
            meta_max = _get_limit(meta, "le", "lt")
            if meta_max is not None:
                max_val = meta_max

        # json_schema_extra can override the limits by hand.
        extra = param_field.json_schema_extra
        if extra and not callable(extra):
            if "ge" in extra:
                min_val = _as_limit(extra["ge"])
            elif "minimum" in extra:
                min_val = _as_limit(extra["minimum"])

            if "le" in extra:
                max_val = _as_limit(extra["le"])
            elif "maximum" in extra:
                max_val = _as_limit(extra["maximum"])

        params_list.append(
            {
                "name": param_name,
                "type": _get_type_info(param_field.annotation),
                "default": serializable_default,
                # The frontend does not need the exact parameter kind. The
                # type info is enough, so all parameters get the same kind.
                "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                "min": min_val,
                "max": max_val,
            }
        )
    return params_list


def _parse_animation_union(union_model: object) -> list[AnimationInfo]:
    animations: list[AnimationInfo] = []
    wrapper_models: tuple[object, ...] = get_args(union_model)

    for wrapper_model in wrapper_models:
        if (
            not inspect.isclass(wrapper_model)
            or not issubclass(wrapper_model, BaseModel)
            or not wrapper_model.model_fields
        ):
            continue

        anim_name, params_field = next(iter(wrapper_model.model_fields.items()))
        params_model: object = params_field.annotation

        title = params_field.title or anim_name.replace("_", " ").title()
        description = params_field.description or wrapper_model.__doc__

        # The preset animation accepts Union[PresetParams, str]. Describe the
        # parameters of the model part.
        if get_origin(params_model):
            for arg in get_args(params_model):
                if inspect.isclass(arg) and issubclass(arg, BaseModel):
                    params_model = arg
                    break

        params_list: list[ParamInfo] = []
        if inspect.isclass(params_model) and issubclass(params_model, BaseModel):
            params_list = _get_params(params_model)

        animations.append(
            {
                "name": anim_name,
                "title": title,
                "description": description,
                "params": params_list,
            }
        )

    animations.sort(key=lambda x: x["name"])
    return animations


@router.get("/")
def get_animations() -> list[AnimationInfo]:
    """List all animations with their parameters.

    Returns:
        The animations, sorted by name.
    """
    return _parse_animation_union(AnimationModel)
