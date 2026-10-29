"""The thread that reads the microphone and publishes `AudioState` snapshots."""

import logging
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol, override

import numpy as np

from ..types import SILENT_AUDIO, AudioState
from . import dsp
from .settings import AudioSettings

if TYPE_CHECKING:
    import sounddevice as sd

_LOG = logging.getLogger(__name__)

RETRY_INTERVAL = 5.0
"""The time in seconds between two attempts to open the device."""


class BlockSource(Protocol):
    """An open input stream that gives blocks of mono samples."""

    def read(self) -> dsp.Samples:
        """Wait for the next block.

        Returns:
            The samples of the block, with values from -1 to 1.
        """
        ...


type StreamOpener = Callable[[AudioSettings], AbstractContextManager[BlockSource]]
"""A function that opens the input stream for the settings."""


def _inputs(device: Mapping[str, object]) -> float:
    channels = device.get("max_input_channels", 0)
    return channels if isinstance(channels, int | float) else 0


def find_device(devices: Sequence[Mapping[str, object]], name: str | int) -> int | None:
    """Find the input device for a name.

    Args:
        devices: The device descriptions of ``sounddevice.query_devices``,
            in the order of their index.
        name: A part of the device name, with any case, or the device index.

    Returns:
        The index of the first input device whose name contains ``name``.
        A name with ``hw:`` comes first, because the other ALSA devices
        resample or mix in software. None if no input device matches.
    """
    if isinstance(name, int):
        return name
    matches = [
        index
        for index, device in enumerate(devices)
        if name.lower() in str(device.get("name", "")).lower() and _inputs(device) > 0
    ]
    direct = [i for i in matches if "hw:" in str(devices[i].get("name", ""))]
    return next(iter(direct or matches), None)


class _SoundDeviceSource:
    """Read blocks from a sounddevice input stream."""

    def __init__(self, stream: "sd.InputStream", block_size: int) -> None:
        self._stream = stream
        self._block_size = block_size

    def read(self) -> dsp.Samples:
        # An overflow loses samples. The next blocks are still valid, so
        # the analysis continues.
        data, _overflowed = self._stream.read(self._block_size)
        return np.asarray(data[:, 0], dtype=np.float64)


class _SoundDeviceStream(AbstractContextManager[BlockSource]):
    """Open and close a sounddevice input stream."""

    def __init__(self, settings: AudioSettings) -> None:
        self._settings = settings
        self._stream: sd.InputStream | None = None

    @override
    def __enter__(self) -> BlockSource:
        # sounddevice loads PortAudio on import. Import it here, so that a
        # missing library is a capture error and not an import error of the
        # whole application.
        import sounddevice  # noqa: PLC0415

        device = find_device(sounddevice.query_devices(), self._settings.device)
        if device is None:
            msg = f"No input device matches {self._settings.device!r}"
            raise OSError(msg)
        stream = sounddevice.InputStream(
            device=device,
            channels=1,
            samplerate=self._settings.sample_rate,
            blocksize=self._settings.block_size,
            dtype="float32",
        )
        try:
            stream.start()
        except Exception:
            stream.close()
            raise
        self._stream = stream
        _LOG.info("Audio capture runs on device %s", device)
        return _SoundDeviceSource(stream, self._settings.block_size)

    @override
    def __exit__(self, *_args: object) -> None:
        if self._stream is not None:
            self._stream.close()
        self._stream = None


def open_sounddevice(settings: AudioSettings) -> AbstractContextManager[BlockSource]:
    """Open the microphone with sounddevice.

    Args:
        settings: The device, the sample rate and the block size.

    Returns:
        The context manager of the stream. It raises an error on enter if
        the device is missing or does not support the settings.
    """
    return _SoundDeviceStream(settings)


class AudioCapture(threading.Thread):
    """Read the microphone in a loop and keep the latest snapshot.

    The thread never stops on an error. It logs the first error of a
    sequence, publishes `SILENT_AUDIO` and tries again after
    `RETRY_INTERVAL` seconds. The LED loop and the API thus continue
    without sound.

    Attributes:
        settings: The capture settings.
        capturing: True while the device gives blocks.
    """

    settings: AudioSettings
    capturing: bool = False

    def __init__(
        self,
        settings: AudioSettings,
        open_stream: StreamOpener = open_sounddevice,
        clock: Callable[[], float] = time.monotonic,
        retry_interval: float = RETRY_INTERVAL,
    ) -> None:
        """Prepare the thread. Call `start` to open the device.

        Args:
            settings: The capture settings.
            open_stream: The function that opens the input stream.
            clock: The clock of the beat times. `latest` gives times on
                this clock.
            retry_interval: The time in seconds between two attempts to
                open the device.
        """
        super().__init__(name="audio-capture", daemon=True)
        self.settings = settings
        self._open_stream = open_stream
        self._clock = clock
        self._retry_interval = retry_interval
        self._stop_event = threading.Event()
        self._snapshot = SILENT_AUDIO
        self._params = dsp.make_params(
            settings.sample_rate, settings.block_size, settings.noise_floor
        )
        self._analysis = dsp.start(self._params)

    def latest(self) -> AudioState:
        """Get the latest snapshot.

        Returns:
            The snapshot of the last block. The beat times use the clock of
            the thread, `time.monotonic` by default.
        """
        return self._snapshot

    def stop(self, timeout: float | None = None) -> None:
        """Tell the thread to stop and wait for it.

        Args:
            timeout: The longest time to wait in seconds. A blocked read of
                the device can take one block.
        """
        self._stop_event.set()
        if self.is_alive():
            self.join(timeout)

    def _capture(self) -> None:
        """Read blocks until the stop or an error."""
        with self._open_stream(self.settings) as source:
            self.capturing = True
            while not self._stop_event.is_set():
                self._analysis = dsp.step(
                    self._params, self._analysis, source.read(), self._clock()
                )
                self._snapshot = self._analysis.snapshot

    @override
    def run(self) -> None:
        """Capture and analyze until `stop` is called."""
        failed = False
        while not self._stop_event.is_set():
            try:
                self._capture()
            except Exception as e:
                # Any error of the device or of PortAudio only stops the
                # sound. Log the first error after a start or a good run,
                # so that a missing device does not fill the log.
                if self.capturing or not failed:
                    _LOG.warning("Audio capture failed, retrying: %s", e)
                failed = True
                self.capturing = False
                self._snapshot = SILENT_AUDIO
                # The next attempt starts with a silent window, but the beat
                # count goes on, so that `beat_switch` does not jump back.
                self._analysis = replace(
                    dsp.start(self._params), beat_count=self._analysis.beat_count
                )
                self._stop_event.wait(self._retry_interval)
        self.capturing = False
