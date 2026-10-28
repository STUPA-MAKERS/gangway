"""The HTTP API for the frontend.

All routes need the API key in the ``X-API-Key`` header.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import animations, config, data, presets, visualization
from .security import get_api_key

app = FastAPI()
"""The FastAPI application."""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dependencies = [Depends(get_api_key)]

app.include_router(
    visualization.router, prefix="/api/visualization", dependencies=dependencies
)
app.include_router(config.router, prefix="/api/config", dependencies=dependencies)
app.include_router(data.router, prefix="/api/data", dependencies=dependencies)
app.include_router(
    animations.router, prefix="/api/animations", dependencies=dependencies
)
app.include_router(presets.router, prefix="/api/presets", dependencies=dependencies)
