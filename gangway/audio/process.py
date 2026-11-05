"""Run the sound capture in a child process.

The LED render loop is Python code that holds the GIL most of the time.
A capture thread in the same process then gets too little time: the input
buffer overflows and loses samples, and the beat tracker loses the tempo.
On the Pi, half of the blocks overflowed. A child process has its own GIL
and can use another core of the Pi.

The child sends each snapshot through a pipe. A thread in the parent reads
the pipe and keeps the latest snapshot. Both processes use
`time.monotonic`, which is the same clock for all processes, so the beat
times need no change.
"""

import logging
import multiprocessing as mp
import threading
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event

from ..types import SILENT_AUDIO, AudioState
from .capture import AudioCapture
from .settings import AudioSettings

_LOG = logging.getLogger(__name__)

# A fork copies the threads and the locks of the parent in an unknown state.
# A spawn starts a new interpreter.
_CONTEXT = mp.get_context("spawn")


def _child(settings: AudioSettings, conn: Connection, stop: Event) -> None:
    """Capture in the child process and send each snapshot to the parent."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    def send(snapshot: AudioState, capturing: bool) -> None:
        conn.send((snapshot, capturing))

    capture = AudioCapture(settings, on_snapshot=send)
    capture.start()
    stop.wait()
    capture.stop(timeout=1.0)
    conn.close()


class AudioProcess:
    """The sound capture in a child process, with the API of `AudioCapture`.

    Attributes:
        settings: The capture settings.
        capturing: True while the device gives blocks.
    """

    settings: AudioSettings
    capturing: bool = False

    def __init__(self, settings: AudioSettings) -> None:
        """Prepare the process. Call `start` to open the device.

        Args:
            settings: The capture settings.
        """
        self.settings = settings
        self._snapshot = SILENT_AUDIO
        self._stop = _CONTEXT.Event()
        receiver, sender = _CONTEXT.Pipe(duplex=False)
        self._receiver = receiver
        self._sender = sender
        self._process = _CONTEXT.Process(
            target=_child,
            args=(settings, sender, self._stop),
            name="audio-capture",
            daemon=True,
        )
        self._reader = threading.Thread(
            target=self._read, name="audio-receiver", daemon=True
        )

    def start(self) -> None:
        """Start the child process and the thread that reads its snapshots."""
        self._process.start()
        # The parent keeps no copy of the send end, so the pipe ends when
        # the child exits.
        self._sender.close()
        self._reader.start()

    def latest(self) -> AudioState:
        """Get the latest snapshot.

        Returns:
            The snapshot of the last block. The beat times use
            `time.monotonic`.
        """
        return self._snapshot

    def is_alive(self) -> bool:
        """Check if the child process runs.

        Returns:
            True while the child process runs.
        """
        return self._process.is_alive()

    def stop(self, timeout: float | None = None) -> None:
        """Tell the child process to stop and wait for it.

        Args:
            timeout: The longest time to wait in seconds. After it, the
                child gets SIGTERM.
        """
        self._stop.set()
        if self._process.pid is None:
            return
        self._process.join(timeout)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout)

    def _read(self) -> None:
        """Keep the latest snapshot from the pipe until the child exits."""
        try:
            while True:
                snapshot, capturing = self._receiver.recv()
                self._snapshot = snapshot
                self.capturing = capturing
        except (EOFError, OSError):
            pass
        if not self._stop.is_set():
            _LOG.warning("The audio capture process stopped")
        self._snapshot = SILENT_AUDIO
        self.capturing = False
