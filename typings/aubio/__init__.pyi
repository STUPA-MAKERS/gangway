"""Type stub for aubio.

The package has no type information. This stub covers the part of the API
that gangway uses.
"""

import numpy as np
from numpy.typing import NDArray

class tempo:  # noqa: N801
    """The online beat tracker of aubio."""

    def __init__(
        self, method: str, buf_size: int, hop_size: int, samplerate: int
    ) -> None:
        """Make a tracker for hops of ``hop_size`` samples."""

    def __call__(self, hop: NDArray[np.float32]) -> NDArray[np.float32]:
        """Analyze one hop. Element 0 is not 0 if the hop holds a beat."""

    def set_silence(self, silence: float) -> int:
        """Set the level in dB below which a hop gives no beat."""

    def get_last(self) -> int:
        """Get the time of the last beat in samples since the start."""

    def get_bpm(self) -> float:
        """Get the current tempo estimate in beats per minute."""

    def get_confidence(self) -> float:
        """Get the confidence of the tempo estimate, from 0 to 1."""
