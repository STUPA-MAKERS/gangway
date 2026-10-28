"""Color helpers for the idle animations."""


def _to_bytes(r: float, g: float, b: float) -> tuple[int, int, int]:
    return int(r * 255), int(g * 255), int(b * 255)


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """Convert a color from HSV to RGB.

    Args:
        h: The hue, from 0 to 1.
        s: The saturation, from 0 to 1.
        v: The value, from 0 to 1.

    Returns:
        The red, green and blue channels, from 0 to 255.
    """
    if s == 0.0:
        return _to_bytes(v, v, v)
    sector = int(h * 6.0)
    f = (h * 6.0) - sector
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    sectors = ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))
    return _to_bytes(*sectors[sector % 6])
