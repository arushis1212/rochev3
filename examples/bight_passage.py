"""Exact centerline passage of a circular yarn bight through a circular ring."""
from dataclasses import asdict, dataclass
import json
import math


@dataclass(frozen=True)
class Passage:
    length_beyond_plane_mm: float
    crossings: tuple
    event: str
    ring_surface_gap_lower_mm: float


def passage(bend_radius, leg_length, ring_radius, ring_tube_radius, yarn_radius,
            center_height, offset=(0., 0.)):
    """Height is the bend circle center's signed distance from the ring plane, in mm."""
    dimensions = (bend_radius, leg_length, ring_radius, ring_tube_radius, yarn_radius)
    cx, cy = offset
    if not all(math.isfinite(v) for v in (*dimensions, center_height, cx, cy)):
        raise ValueError("Geometry must be finite")
    if min(dimensions) <= 0 or ring_tube_radius >= ring_radius:
        raise ValueError("Radii and lengths must describe a ring with an open bore")

    a, h = bend_radius, center_height
    max_radial = math.hypot(abs(cx) + a, cy)
    gap = ring_radius - max_radial - ring_tube_radius - yarn_radius
    # Follow material from the left leg towards the bend, then back on the right leg.
    points = ()
    arc_length = math.pi * a
    if h <= -a:
        length = 0.
        event = "tip tangent to plane" if h == -a else "approaching"
    elif h >= leg_length:
        length = arc_length + 2 * leg_length
        event = "endpoints in plane" if h == leg_length else "fully through plane"
    else:
        if h < 0:
            half_width = math.sqrt((a + h) * (a - h))
            length = 2 * a * math.acos(-h / a)
        else:
            half_width = a
            length = arc_length + 2 * h
        points = tuple((x, cy, sign) for x, sign in ((cx - half_width, 1),
                                                     (cx + half_width, -1))
                       if math.hypot(x, cy) < ring_radius)
        event = "transverse plane intersections"
    return Passage(length, points, event, gap)


if __name__ == "__main__":
    print(json.dumps(asdict(passage(2., 15., 6., .6, .25, -1.)), indent=2))
