"""Type stub for sounddevice.

The package has no type information. This stub covers the part of the API
that gangway uses.
"""

from typing import Literal, Self

import numpy as np
from numpy.typing import NDArray

__version__: str

class PortAudioError(Exception):
    """An error of PortAudio."""

class DeviceList(tuple[dict[str, object], ...]):
    """The descriptions of all devices, in the order of their index."""

def query_devices() -> DeviceList:
    """Get the descriptions of all devices."""

class InputStream:
    """A PortAudio input stream."""

    def __init__(
        self,
        samplerate: float | None = None,
        blocksize: int | None = None,
        device: int | str | None = None,
        channels: int | None = None,
        dtype: Literal["float32", "int16"] | None = None,
    ) -> None:
        """Open the stream."""

    def start(self) -> None:
        """Start the capture."""

    def stop(self) -> None:
        """Stop the capture."""

    def close(self) -> None:
        """Close the stream."""

    def read(self, frames: int) -> tuple[NDArray[np.float32], bool]:
        """Wait for samples.

        Returns:
            The samples with one column for each channel, and True if
            samples were lost.
        """

    def __enter__(self) -> Self: ...
    def __exit__(self, *args: object) -> None: ...
