"""Animations that combine or change other animations."""

from .alternate import alternate
from .blend import blend
from .by_strip import by_strip, strip_assignment
from .exponential_at import exponential_at
from .extrapolate import extrapolate
from .persist import persist
from .preset import preset
from .proximity import proximity, proximity_speed
from .schedule import day_of_week, schedule
from .smooth import smooth

__all__ = [
    "alternate",
    "blend",
    "by_strip",
    "day_of_week",
    "exponential_at",
    "extrapolate",
    "persist",
    "preset",
    "proximity",
    "proximity_speed",
    "schedule",
    "smooth",
    "strip_assignment",
]
