"""MQTT client that lets Home Assistant select the animation preset."""

import asyncio
import json
import logging
from pathlib import Path

import aiomqtt
import yaml

from .config import CONFIG, ConfigFile
from .state import STATE
from .types import YamlValue

logger = logging.getLogger(__name__)

PRESETS_DIR = CONFIG.path.parent / "presets"
"""The directory of the preset files."""


class MQTTHandler:
    """Publish the preset selector to Home Assistant and apply preset changes.

    Attributes:
        connected: True while the client has a broker connection.
        client: The active client, or None before the first connection.
    """

    def __init__(self) -> None:
        """Make a handler. Call `start` to connect."""
        self.connected = False
        self.client: aiomqtt.Client | None = None

    async def start(self) -> None:
        """Connect to the broker and process messages until cancelled.

        The handler connects again 5 seconds after each connection error.
        """
        if not CONFIG.MQTT_HOST:
            logger.info("MQTT host not configured, skipping MQTT start.")
            return

        logger.info(
            f"Starting MQTT Handler connecting to {CONFIG.MQTT_HOST}:{CONFIG.MQTT_PORT}"
        )

        while True:
            try:
                async with aiomqtt.Client(
                    hostname=CONFIG.MQTT_HOST,
                    port=CONFIG.MQTT_PORT,
                    username=CONFIG.MQTT_USERNAME,
                    password=CONFIG.MQTT_PASSWORD,
                ) as client:
                    self.client = client
                    self.connected = True
                    logger.info("Connected to MQTT Broker")

                    await self._publish_discovery()
                    await self._subscribe_command()

                    await client.publish(
                        f"{CONFIG.MQTT_TOPIC_PREFIX}/status",
                        "online",
                        retain=True,
                    )

                    async for message in client.messages:
                        await self._handle_message(message)

            except aiomqtt.MqttError as e:
                logger.error(f"MQTT Error: {e}")
                self.connected = False
            except Exception as e:
                logger.error(f"Unexpected error in MQTT loop: {e}")
                self.connected = False

            logger.info("MQTT Disconnected. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

    async def _publish_discovery(self) -> None:
        presets = self._get_presets()
        device_info = {
            "identifiers": ["gangway_led_controller"],
            "name": "Gangway LED Controller",
            "manufacturer": "STUPA MAKERS",
            "model": "G.A.N.G.W.A.Y",
        }

        config_payload = {
            "name": "Animation Preset",
            "unique_id": "gangway_animation_preset",
            "command_topic": f"{CONFIG.MQTT_TOPIC_PREFIX}/preset/set",
            "state_topic": f"{CONFIG.MQTT_TOPIC_PREFIX}/preset/state",
            "options": presets,
            "device": device_info,
            "availability_topic": f"{CONFIG.MQTT_TOPIC_PREFIX}/status",
        }

        # Home Assistant needs a node ID that is unique for each device.
        node_id = CONFIG.MQTT_TOPIC_PREFIX
        if self.client is not None:
            await self.client.publish(
                f"homeassistant/select/{node_id}/preset/config",
                json.dumps(config_payload),
                retain=True,
            )

    async def _subscribe_command(self) -> None:
        if self.client is not None:
            await self.client.subscribe(f"{CONFIG.MQTT_TOPIC_PREFIX}/preset/set")

    async def _handle_message(self, message: aiomqtt.Message) -> None:
        topic = message.topic
        payload = message.payload.decode()

        if topic.matches(f"{CONFIG.MQTT_TOPIC_PREFIX}/preset/set"):
            logger.info(f"Received preset switch request: {payload}")
            if await self._load_preset(payload) and self.client is not None:
                await self.client.publish(
                    f"{CONFIG.MQTT_TOPIC_PREFIX}/preset/state",
                    payload,
                    retain=True,
                )

    def _get_presets(self) -> list[str]:
        PRESETS_DIR.mkdir(exist_ok=True)
        return [p.stem for p in PRESETS_DIR.glob("*.yaml")]

    async def _load_preset(self, name: str) -> bool:
        preset_path = PRESETS_DIR / f"{name}.yaml"
        if not preset_path.exists():
            logger.error(f"Preset {name} not found")
            return False

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._apply_preset_sync, preset_path)
        except Exception as e:
            logger.error(f"Failed to load preset {name}: {e}")
            return False
        return True

    def _apply_preset_sync(self, preset_path: Path) -> None:
        # This runs in an executor thread because file I/O and the animation
        # parse block the event loop.
        with open(preset_path) as f:
            animation_data: YamlValue = yaml.safe_load(f)

        # Read the config again so that the other sections stay the same.
        with open(CONFIG.path) as f:
            config_data: ConfigFile = yaml.safe_load(f)

        config_data["animation"] = animation_data

        with open(CONFIG.path, "w") as f:
            yaml.dump(config_data, f, sort_keys=False)

        CONFIG.load()

        if STATE.led_controller:
            STATE.led_controller.reload_config()
