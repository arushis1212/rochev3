"""Detect contact between finite yarn and a cubic forming face. Lengths are mm."""
import json
from pathlib import Path

import numpy as np
from numpy.polynomial import Polynomial


def closest_gap(data, endpoints):
    """Return the signed clearance, yarn fraction and point on the cubic face."""
    ends = np.asarray(endpoints, dtype=float)
    line = ends[1] - ends[0]
    xy_norm_squared = line[:2] @ line[:2]
    if ends.shape != (2, 3) or xy_norm_squared <= 0:
        raise ValueError("A finite edge with a nonzero in-plane projection is required")
    x = Polynomial([0, 1])
    u = data["face_start_u_mm"] + data["face_span_mm"] * x
    v = data["high_v_mm"] - data["drop_mm"] * (3*x*x - 2*x*x*x)
    dx, dy = u - ends[0, 0], v - ends[0, 1]
    fraction = (line[0]*dx + line[1]*dy) / xy_norm_squared
    # A constrained minimum occurs on an endpoint branch, on the interior
    # projection branch, or where the projection enters or leaves the segment.
    roots_of = [fraction, fraction-1]
    for s in (0, 1, fraction):
        bx, by = dx-line[0]*s, dy-line[1]*s
        roots_of.append(bx*u.deriv()+by*v.deriv())
    candidates = [0., 1.]
    for p in roots_of:
        candidates.extend(z.real for z in p.roots()
                          if abs(z.imag) < 1e-9 and 0 <= z.real <= 1)
    curve = np.asarray(candidates)
    along = np.clip(fraction(curve), 0., 1.)
    yarn = ends[0] + along[:, None]*line
    surface = np.column_stack((u(curve), v(curve), yarn[:, 2]))
    distance = np.linalg.norm(yarn-surface, axis=1)
    best = np.argmin(distance)
    if abs(yarn[best, 2]) > data["face_half_width_mm"]:
        raise ValueError("Closest projected point is outside the finite face width")
    return float(distance[best]-data["yarn_radius_mm"]), float(along[best]), surface[best]


def clearance_at(data, path, ns):
    if not 0 <= ns <= path["clock_ns"]:
        raise ValueError("Time outside the supplied motion interval")
    t = ns*1e-9
    endpoints = (np.array(path["position_mm"]) + 1000*t*np.array(path["velocity_m_s"])
                 + 500*t*t*np.array(path["acceleration_m_s2"]))
    return closest_gap(data, endpoints)


def crossing(data, path):
    """Bracket a sign-changing clearance root on the supplied incoming trajectory."""
    low, high = 0., float(path["clock_ns"])
    if clearance_at(data, path, low)[0] <= 0 or clearance_at(data, path, high)[0] >= 0:
        raise ValueError("Incoming trajectory must bracket the contact")
    while high-low > 1e-6:
        middle = (low+high)*.5
        if clearance_at(data, path, middle)[0] > 0:
            low = middle
        else:
            high = middle
    _, fraction, point = clearance_at(data, path, high)
    return path["start_us"]+high*.001, fraction, point


if __name__ == "__main__":
    data = json.loads(Path(__file__).with_name("working_edge.json").read_text())
    for path in data["paths"]:
        time, fraction, point = crossing(data, path)
        print(f'{path["clock_ns"]} ns incoming step: contact at {time:.9f} µs, '
              f'yarn fraction {fraction:.9f}, gate UVW {point.round(6)} mm.')
