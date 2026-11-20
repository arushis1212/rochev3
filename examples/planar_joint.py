"""Normal pressure and shear on a fully seated planar joint with uniform foundation stiffness.

Coordinates y,z are in mm relative to the area centroid. Forces and moments use N and N mm.
"""
from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class Footprint:
    area: float
    yy: float  # integral y² dA
    yz: float  # integral yz dA
    zz: float  # integral z² dA

    def __post_init__(self):
        if (not all(map(isfinite, (self.area, self.yy, self.yz, self.zz)))
                or min(self.area, self.yy, self.zz) <= 0 or self.yy*self.zz <= self.yz**2):
            raise ValueError("Positive area and positive-definite central area moments required")


@dataclass(frozen=True)
class JointLoad:
    normal: float
    first_y: float  # required integral y*p dA
    first_z: float  # required integral z*p dA
    shear_y: float
    shear_z: float
    twist: float  # required integral (y*shear_z - z*shear_y) dA

    def __post_init__(self):
        if not all(map(isfinite, vars(self).values())):
            raise ValueError("Finite joint forces and moments required")


def traction(foot, load, y, z):
    """Signed normal compression and the two in-plane shear components in N/mm²."""
    if not all(map(isfinite, (y, z))):
        raise ValueError("Finite section coordinates required")
    determinant = foot.yy*foot.zz - foot.yz**2
    slope_y = (foot.zz*load.first_y - foot.yz*load.first_z)/determinant
    slope_z = (foot.yy*load.first_z - foot.yz*load.first_y)/determinant
    spin = load.twist/(foot.yy+foot.zz)
    return (load.normal/foot.area + slope_y*y + slope_z*z,
            load.shear_y/foot.area - spin*z,
            load.shear_z/foot.area + spin*y)


def bounds(foot, load, y_bounds, z_bounds):
    """Conservative pressure bounds and sufficient static friction over a containing rectangle."""
    if y_bounds[0] >= y_bounds[1] or z_bounds[0] >= z_bounds[1]:
        raise ValueError("Increasing coordinate bounds required")
    values = [traction(foot, load, y, z) for y in y_bounds for z in z_bounds]
    minimum = min(p for p, _, _ in values)
    maximum = max(p for p, _, _ in values)
    friction = max(hypot(sy, sz)/p for p, sy, sz in values) if minimum > 0 else None
    return minimum, maximum, friction
