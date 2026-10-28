"""Color helpers for the idle animations."""


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
        return int(v * 255), int(v * 255), int(v * 255)
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)
