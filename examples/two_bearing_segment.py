"""Static load sharing by two round pins supporting one straight yarn element."""
from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class Contact:
    fraction: float
    clearance_mm: float
    normal: tuple


def closest_pin_contact(start, end, pin, yarn_radius, pin_radius):
    """Return the closest fraction and surface gap of a finite 2D yarn segment."""
    ax, ay = start
    bx, by = end
    cx, cy = pin
    if not all(map(isfinite, (ax, ay, bx, by, cx, cy, yarn_radius, pin_radius))):
        raise ValueError("Coordinates and radii must be finite")
    if min(yarn_radius, pin_radius) <= 0 or (ax == bx and ay == by):
        raise ValueError("Segment length and radii must be positive")
    dx, dy = bx-ax, by-ay
    t = max(0., min(1., ((cx-ax)*dx+(cy-ay)*dy)/(dx*dx+dy*dy)))
    nx, ny = ax+t*dx-cx, ay+t*dy-cy
    distance = hypot(nx, ny)
    if distance == 0:
        raise ValueError("No unique normal at a pin center")
    return Contact(t, distance-yarn_radius-pin_radius, (nx/distance, ny/distance))


def bearing_loads(t1, t2, left_load, right_load):
    """Return upward pin reactions for two parallel normals and downward nodal loads."""
    if not all(map(isfinite, (t1, t2, left_load, right_load))):
        raise ValueError("Fractions and forces must be finite")
    if not 0 <= t1 < t2 <= 1 or min(left_load, right_load) < 0:
        raise ValueError("Use ordered, distinct contacts and nonnegative downward loads")
    total = left_load+right_load
    second = (right_load-t1*total)/(t2-t1)
    first = total-second
    if min(first, second) < 0:
        raise ValueError("The specified load would lift one of the two bearings")
    return first, second


if __name__ == "__main__":
    contacts = [closest_pin_contact((0., 0.), (8., 0.), (x, -.9), .3, .6) for x in (2.,6.)]
    f1, f2 = bearing_loads(*(c.fraction for c in contacts), 2.5, 3.5)
    print(f"Pin loads at 2 and 6 mm: {f1:g} mN and {f2:g} mN")
