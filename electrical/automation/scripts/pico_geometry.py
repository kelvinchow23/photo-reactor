"""Pico WH socket geometry, origin at module centre, USB at negative Y.

Antenna is at the opposite (+Y) end. The 14 x 9 mm board opening follows
the Pico W datasheet keep-out area (section 2.2.1), between socket rows.
"""
ANTENNA_CUTOUT = (-7.0, 16.5, 7.0, 25.5)


def antenna_cutout(cx, cy):
    x1, y1, x2, y2 = ANTENNA_CUTOUT
    return cx + x1, cy + y1, cx + x2, cy + y2
