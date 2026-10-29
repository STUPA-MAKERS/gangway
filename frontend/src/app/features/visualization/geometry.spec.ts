import { containFit, invert3, project, segmentDistance2 } from './geometry';

describe('geometry', () => {
  it('inverts a homography', () => {
    const m = [
      [2, 0, 10],
      [0, 3, 5],
      [0.001, 0, 1],
    ];
    const inv = invert3(m);
    expect(inv).not.toBeNull();
    const [x, y] = project(40, 60, m);
    const [bx, by] = project(x, y, inv);
    expect(bx).toBeCloseTo(40);
    expect(by).toBeCloseTo(60);
  });

  it('refuses a singular matrix', () => {
    expect(
      invert3([
        [1, 2, 3],
        [2, 4, 6],
        [0, 0, 1],
      ]),
    ).toBeNull();
  });

  it('keeps the point with no matrix', () => {
    expect(project(3, 4, null)).toEqual([3, 4]);
  });

  it('fits an image like object-fit: contain', () => {
    expect(containFit(200, 100, 100, 100)).toEqual({ width: 100, height: 100, x: 50, y: 0 });
    expect(containFit(100, 200, 100, 100)).toEqual({ width: 100, height: 100, x: 0, y: 50 });
  });

  it('measures the distance to a segment', () => {
    expect(segmentDistance2(5, 3, 0, 0, 10, 0)).toBe(9);
    expect(segmentDistance2(-3, 4, 0, 0, 10, 0)).toBe(25);
    expect(segmentDistance2(1, 1, 0, 0, 0, 0)).toBe(2);
  });
});
