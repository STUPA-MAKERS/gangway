"""Project points from the camera image to the floor plan."""

from collections.abc import Sequence

import cv2
import numpy as np
from numpy.typing import ArrayLike, NDArray

from .. import config


def get_homography(
    src: ArrayLike | None = None, dst: ArrayLike | None = None
) -> NDArray[np.float64]:
    """Calculate the 3x3 homography matrix from four point pairs.

    Args:
        src: Four points in the camera image, with the shape (4, 2). The
            default is the ``src_points`` of the config.
        dst: The four matching floor points, with the shape (4, 2). The
            default is the ``dst_points`` of the config.

    Returns:
        The matrix that maps image points to floor points.
    """
    if src is None:
        src = np.array(config.CONFIG.SRC_POINTS)
    if dst is None:
        dst = np.array(config.CONFIG.DST_POINTS)

    return np.asarray(
        cv2.getPerspectiveTransform(
            np.array(src, dtype=np.float32), np.array(dst, dtype=np.float32)
        ),
        dtype=np.float64,
    )


def apply_transform(
    points: Sequence[tuple[float, float]] | NDArray[np.floating],
    matrix: NDArray[np.float64] | None = None,
) -> NDArray[np.float64]:
    """Apply a homography matrix to a list of points.

    Args:
        points: The points, with the shape (N, 2).
        matrix: The homography matrix. The default is the matrix from the
            config.

    Returns:
        The projected points, with the shape (N, 2).
    """
    if matrix is None:
        matrix = get_homography()
    points_homo = np.pad(points, ((0, 0), (0, 1)), constant_values=1)

    transformed = points_homo @ matrix.T

    return transformed[:, :2] / transformed[:, 2, np.newaxis]
