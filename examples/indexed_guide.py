"""Exact planar geometry of successive whole-notch moves along a desired line."""
from fractions import Fraction
from math import hypot, isfinite, sqrt


def indexed_path(dx, dy):
    """Displacements are rational multiples of one notch. Return time and position at each move."""
    if any(isinstance(value, (bool, float)) for value in (dx, dy)):
        raise ValueError("Use integers, rational strings, or Fraction objects for exact ties")
    delta = (Fraction(dx), Fraction(dy))
    events = []
    for axis, travel in enumerate(delta):
        if not travel:
            continue
        length = abs(travel)
        steps = int(length + Fraction(1, 2))
        direction = 1 if travel > 0 else -1
        for index in range(steps):
            time = Fraction(2*index+1, 2)/length
            events.append((time, axis, direction))
    # When both thresholds coincide, turn X first, then Y.
    events.sort()
    x = y = 0
    yield Fraction(0), x, y
    for time, axis, sign in events:
        yield time, x, y
        if axis == 0:
            x += sign
        else:
            y += sign
        yield time, x, y
    yield Fraction(1), x, y


def envelope(dx, dy, notch_mm):
    """Maximum transverse deviation from the line and maximum distance to the synchronized target."""
    if not isfinite(notch_mm) or notch_mm <= 0:
        raise ValueError("One notch needs a finite positive length")
    points = list(indexed_path(dx, dy))
    dx, dy = Fraction(dx), Fraction(dy)
    tangent = hypot(dx, dy)
    max_cross = Fraction(0)
    max_distance_squared = Fraction(0)
    for time, x, y in points:
        max_cross = max(max_cross, abs(dx*y-dy*x))
        error_x, error_y = x-time*dx, y-time*dy
        max_distance_squared = max(max_distance_squared, error_x**2+error_y**2)
    return {
        "notches": (len(points)-2)//2,
        "last_notch": points[-1][1:],
        "maximum_cross_track_mm": notch_mm*float(max_cross)/tangent if tangent else 0.,
        "maximum_synchronized_error_mm": notch_mm*sqrt(max_distance_squared),
    }


if __name__ == "__main__":
    print(envelope(3, 4, 1.))
