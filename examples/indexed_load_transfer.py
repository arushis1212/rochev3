"""Quasistatic load transfer between a rear shoe and an end stop. Units: mm and N."""
from dataclasses import dataclass
from math import isfinite


def finite(*values):
    if not all(isfinite(value) for value in values):
        raise ValueError("Inputs must be finite")


@dataclass(frozen=True)
class ContactState:
    carriage: float
    rear_force: float
    stop_force: float
    rear_gap: float
    stop_gap: float


def loaded_position(housing, stop_position, support_force, rear_compliance, stop_compliance):
    """Solve the two unilateral linear contacts at the specified load."""
    finite(housing, stop_position, support_force, rear_compliance, stop_compliance)
    if min(support_force, rear_compliance, stop_compliance) <= 0:
        raise ValueError("Positive support force and two finite positive compliances required")
    offset = housing - stop_position
    share = (offset + support_force * rear_compliance) / (rear_compliance + stop_compliance)
    stop = min(support_force, max(0., share))
    rear = support_force - stop
    carriage = min(housing + rear_compliance * rear, stop_position + stop_compliance * stop)
    return ContactState(carriage, rear, stop,
                        max(0., housing - carriage + rear_compliance * rear),
                        max(0., stop_position - carriage + stop_compliance * stop))


def common_housing_window(stop_position, gap_limits, compression_limits, *, loaded):
    """Absolute housing positions that satisfy a gap over all admitted compressions."""
    low, high = gap_limits
    cmin, cmax = compression_limits
    finite(stop_position, low, high, cmin, cmax)
    if low <= 0 or high < low or cmin < 0 or cmax < cmin:
        raise ValueError("Invalid positive gap or nonnegative compression interval")
    if loaded == "rear":
        result = (stop_position-high-cmin, stop_position-low-cmax)
    elif loaded == "stop":
        result = (stop_position+low+cmax, stop_position+high+cmin)
    else:
        raise ValueError("Choose the rear or stop contact")
    return result if result[0] <= result[1] else None


def selectable_indices(positions, window):
    """Look up the actual fully engaged indices; preserve their original numbering."""
    values = tuple(positions)
    finite(*values)
    if len(values) < 2 or any(b <= a for a,b in zip(values,values[1:])):
        raise ValueError("At least two strictly increasing measured index positions required")
    if window is None:
        return []
    finite(*window)
    if window[1] < window[0]:
        raise ValueError("Inverted index window")
    return [i for i,h in enumerate(values) if window[0] <= h <= window[1]]


if __name__=="__main__":
    for housing in (-.02, -.002, 0., .002, .24):
        s = loaded_position(housing, 0., 8., .0005, .0001)
        print(f"h = {housing: .4f} mm, rear = {s.rear_force:.3f} N, stop = {s.stop_force:.3f} N, carriage = {s.carriage:.6f} mm")
