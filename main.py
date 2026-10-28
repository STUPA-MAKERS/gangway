#!/usr/bin/env python3
"""Start the gangway LED controller.

The program starts the LED render thread, the Xovis receiver on port 8081
and the API on port 8082. It runs until Ctrl+C.
"""

import argparse
import asyncio
import contextlib
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

from gangway import config
from gangway.api import app
from gangway.led_controller import LEDController
from gangway.state import STATE
from gangway.types import TrackedPoint
from gangway.xovis.server import XOVISServer


async def main() -> None:
    """Start all components and stop them when the API server stops."""
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, help="Path to config.yaml")
    args = parser.parse_args()
    config_path: Path | None = args.config

    if config_path:
        config.CONFIG.path = config_path
        config.CONFIG.load()

    print("Starting components...")

    led_controller = LEDController()
    STATE.led_controller = led_controller
    led_controller.start()

    xovis_server = XOVISServer()
    STATE.xovis_server = xovis_server
    xovis_server.subscribe_position(led_controller.update_objects)

    def update_api_objects(new_objects: list[TrackedPoint]) -> None:
        STATE.objects = new_objects

    xovis_server.subscribe_position(update_api_objects)

    xovis_http_server = xovis_server.start_server()

    # Uvicorn owns the signal handling. On Ctrl+C it shuts down and serve()
    # returns, so the cleanup below always runs.
    config_uvicorn = uvicorn.Config(app, host="0.0.0.0", port=8082, log_level="info")
    server = uvicorn.Server(config_uvicorn)

    try:
        await server.serve()
    except asyncio.CancelledError:
        pass
    finally:
        print("\nShutting down background components...")

        try:
            xovis_http_server.shutdown()
            print("XOVIS callback handler stopped.")
        except Exception as e:
            print(f"Error stopping Xovis: {e}")

        try:
            led_controller.stop()
            print("LED Controller stopped.")
        except Exception as e:
            print(f"Error stopping LED Controller: {e}")


if __name__ == "__main__":
    # Uvicorn can miss an interrupt that arrives during the startup or the
    # shutdown.
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
