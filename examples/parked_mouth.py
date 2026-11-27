"""Minimum working yarn length to a parked guide mouth. Distances in mm."""
from math import cos, radians, sin

try:
    from .guide_length import disk_distance
except ImportError:  # Also allow python3 examples/parked_mouth.py.
    from guide_length import disk_distance


def parked_mouth():
    anchor = (113.62171667905795, 158.57109616640963, 69.4009085386171)
    mouth = (136.0, 190.0, 96.5367498391805)
    tilt = radians(20)
    normal = (0.0, cos(tilt), sin(tilt))
    original_span = 1032.3550936967192 - 999.1745770950396
    reach = disk_distance(anchor, mouth, normal, 0.43815)
    return reach, original_span, reach - original_span


if __name__ == "__main__":
    reach, span, slide = parked_mouth()
    print(f"Minimum reach {reach:.3f} mm")
    print(f"Reference material span {span:.3f} mm")
    print(f"Minimum additional material for inextensible yarn {slide:.3f} mm")
