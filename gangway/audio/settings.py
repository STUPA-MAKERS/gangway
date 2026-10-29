"""The settings of the sound capture, from the ``audio`` section of the config."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypedDict


class AudioConfig(TypedDict, total=False):
    """The ``audio`` section of the config file.

    Attributes:
        enabled: Set to false to not open the microphone.
        device: A part of the device name, or the device index.
        sample_rate: The sample rate in hertz.
        block_size: The number of samples in a block.
        noise_floor: The RMS value that counts as silence, as a part of the
            full scale.
    """

    enabled: bool
    device: str | int
    sample_rate: int
    block_size: int
    noise_floor: float


@dataclass(frozen=True)
class AudioSettings:
    """The settings of the sound capture.

    Attributes:
        enabled: Whether to open the microphone.
        device: A part of the device name, or the device index. The default
            is the name of the ALSA card of the USB microphone.
        sample_rate: The sample rate in hertz. The device must support it.
        block_size: The number of samples in a block. 512 samples at
            22050 Hz give about 43 blocks per second.
        noise_floor: The RMS value that counts as silence, as a part of the
            full scale. 0.01 is -40 dBFS.
    """

    enabled: bool = True
    device: str | int = "AK5371"
    sample_rate: int = 22050
    block_size: int = 512
    noise_floor: float = 0.01


def _invalid(key: str, value: object) -> TypeError:
    return TypeError(f"The audio setting '{key}' is not valid: {value!r}")


# bool is a subclass of int, so each check for a number rejects a bool.


def _bool(values: Mapping[str, object], key: str, default: bool) -> bool:
    value = values.get(key, default)
    if not isinstance(value, bool):
        raise _invalid(key, value)
    return value


def _int(values: Mapping[str, object], key: str, default: int) -> int:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _invalid(key, value)
    return value


def _float(values: Mapping[str, object], key: str, default: float) -> float:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise _invalid(key, value)
    return float(value)


def _device(values: Mapping[str, object], key: str, default: str | int) -> str | int:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, str | int):
        raise _invalid(key, value)
    return value


def parse_settings(section: Mapping[str, object] | None) -> AudioSettings:
    """Read the settings from the ``audio`` section of the config.

    Args:
        section: The section. None or a missing key gives the default.

    Returns:
        The settings.

    Raises:
        TypeError: If a value has the wrong type, or if a number is out of
            range.
        ValueError: If the section has an unknown key.
    """
    values = section or {}
    unknown = set(values) - set(AudioConfig.__annotations__)
    if unknown:
        msg = f"Unknown audio settings: {', '.join(sorted(unknown))}"
        raise ValueError(msg)

    defaults = AudioSettings()
    return AudioSettings(
        enabled=_bool(values, "enabled", defaults.enabled),
        device=_device(values, "device", defaults.device),
        sample_rate=_int(values, "sample_rate", defaults.sample_rate),
        block_size=_int(values, "block_size", defaults.block_size),
        noise_floor=_float(values, "noise_floor", defaults.noise_floor),
    )
