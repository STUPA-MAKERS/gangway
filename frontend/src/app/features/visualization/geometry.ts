/**
 * Pure geometry for the live view: the homography between the camera image and the floor
 * plan, and the hit test of the strips.
 */

export type Matrix3 = number[][];

/**
 * Inverts a 3x3 matrix and scales it so that the last entry is 1. Returns null for a
 * singular matrix.
 */
export function invert3(m: Matrix3): Matrix3 | null {
  const det =
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
    m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
    m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  if (Math.abs(det) < 1e-10) return null;
  const id = 1 / det;
  const res = [
    [
      (m[1][1] * m[2][2] - m[1][2] * m[2][1]) * id,
      (m[0][2] * m[2][1] - m[0][1] * m[2][2]) * id,
      (m[0][1] * m[1][2] - m[0][2] * m[1][1]) * id,
    ],
    [
      (m[1][2] * m[2][0] - m[1][0] * m[2][2]) * id,
      (m[0][0] * m[2][2] - m[0][2] * m[2][0]) * id,
      (m[0][2] * m[1][0] - m[0][0] * m[1][2]) * id,
    ],
    [
      (m[1][0] * m[2][1] - m[1][1] * m[2][0]) * id,
      (m[0][1] * m[2][0] - m[0][0] * m[2][1]) * id,
      (m[0][0] * m[1][1] - m[0][1] * m[1][0]) * id,
    ],
  ];
  const norm = res[2][2];
  return res.map((row) => row.map((v) => v / norm));
}

/** Applies a homography to a point. With no matrix the point stays. */
export function project(x: number, y: number, m: Matrix3 | null): [number, number] {
  if (!m) return [x, y];
  const w = m[2][0] * x + m[2][1] * y + m[2][2];
  return [(m[0][0] * x + m[0][1] * y + m[0][2]) / w, (m[1][0] * x + m[1][1] * y + m[1][2]) / w];
}

/** The box of an image with `object-fit: contain` in a container. */
export interface Fit {
  width: number;
  height: number;
  x: number;
  y: number;
}

export function containFit(cw: number, ch: number, iw: number, ih: number): Fit {
  const ca = cw / ch;
  const ia = iw / ih;
  if (ca > ia) {
    const height = ch;
    const width = height * ia;
    return { width, height, x: (cw - width) / 2, y: 0 };
  }
  const width = cw;
  const height = width / ia;
  return { width, height, x: 0, y: (ch - height) / 2 };
}

/** The squared distance from a point to a line segment. */
export function segmentDistance2(
  px: number,
  py: number,
  sx: number,
  sy: number,
  ex: number,
  ey: number,
): number {
  const l2 = (sx - ex) ** 2 + (sy - ey) ** 2;
  let t = l2 === 0 ? 0 : ((px - sx) * (ex - sx) + (py - sy) * (ey - sy)) / l2;
  t = Math.max(0, Math.min(1, t));
  return (px - (sx + t * (ex - sx))) ** 2 + (py - (sy + t * (ey - sy))) ** 2;
}
