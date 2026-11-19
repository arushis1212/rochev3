"""Calculate across-flats tolerances for the straight section of a hex drive."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class FitBudget:
    minimum_driver_mm: float
    maximum_driver_mm: float

    @property
    def manufacturing_width_mm(self):
        return self.maximum_driver_mm - self.minimum_driver_mm


def drive_budget(socket_min_mm, socket_max_mm, center_limit_mm, eccentricity_mm,
                reach_mm, clock_deg=0.0, tilt_deg=0.0):
    """Return the lower centering bound and conservative upper entry bound.

    Lengths are in millimetres. Clock is the rotation about the drive axis
    from aligned flats. Tilt is the angle between the tool and socket axes.
    Reach is the greatest axial distance over which tilt can displace the center.
    """
    inputs = (socket_min_mm, socket_max_mm, center_limit_mm, eccentricity_mm,
              reach_mm, clock_deg, tilt_deg)
    if not all(math.isfinite(value) for value in inputs):
        raise ValueError('All dimensions and angles must be finite')
    if not 0.0 < socket_min_mm <= socket_max_mm:
        raise ValueError('The socket interval must be positive and ordered')
    if min(center_limit_mm, eccentricity_mm, reach_mm) < 0.0:
        raise ValueError('Center limit, eccentricity and reach must be nonnegative')
    if not (0 <= clock_deg <= 30 and 0 <= tilt_deg < 90):
        raise ValueError('Clock must be in [0, 30] degrees and tilt in [0, 90)')

    clock = math.radians(clock_deg)
    tilt = math.radians(tilt_deg)
    root_three = math.sqrt(3)
    face_support = (math.cos(clock) + math.sin(clock) / root_three) / 2
    tilt_allowance = (1 / math.cos(tilt) - 1 + math.sin(tilt) * math.tan(tilt)) / root_three
    upper = (socket_min_mm / 2 - eccentricity_mm - reach_mm * math.tan(tilt)) / (face_support + tilt_allowance)
    lower = socket_max_mm - root_three * (center_limit_mm - eccentricity_mm)
    return FitBudget(lower, upper)


if __name__ == '__main__':
    budget = drive_budget(2.550, 2.551, 0.010, 0.0005, 1.435, 0.2, 0.15)
    print(f'Driver interval: {budget.minimum_driver_mm:.9f} to {budget.maximum_driver_mm:.9f} mm')
    print(f'Available width: {1000 * budget.manufacturing_width_mm:.6f} micrometres')
