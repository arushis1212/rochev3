"""Continuous finite-radius yarn clearance on an analytical coil-opening example."""
import json

import numpy as np

from physics.roche_contact3d import closest_segments, self_pairs


RESERVE_MM = 1.0e-8


def midpoint_bounds(points, diameter):
    """Return a separating-plane lower bound and feasible-point upper bound."""
    a, b, c, d = points
    u, v = b - a, d - c
    uu, vv = u @ u, v @ v
    if uu == 0.0 or vv == 0.0:
        s = 0.0 if uu == 0.0 else np.clip((c - a) @ u / uu, 0, 1)
        t = 0.0 if vv == 0.0 else np.clip((a - c) @ v / vv, 0, 1)
    else:
        _, _, s_array, t_array = closest_segments(
            a[None], b[None], c[None], d[None]
        )
        s, t = float(s_array[0]), float(t_array[0])
    separation = (a - c) + s * u - t * v
    length = float(np.linalg.norm(separation))
    if length == 0:
        return -diameter, -diameter
    # Every difference between points on the two segments is a convex
    # combination of these four differences. Projection onto any unit vector
    # gives a lower bound, including for almost-parallel segments.
    axis = separation / length
    support = min(float(delta @ axis) for delta in (a-c, a-d, b-c, b-d))
    return max(0.0, support) - diameter, length - diameter


def narrow_interval(start, finish, diameter, allowance, max_depth):
    """Certify one segment pair over one affine time interval, or give a witness."""
    delta = finish - start
    speed = max(np.linalg.norm(x-y) for x in delta[:2] for y in delta[2:])
    pending = [(0.0, 1.0, 0)]
    lower_bounds = []
    while pending:
        lo, hi, depth = pending.pop()
        mid = (lo + hi) / 2
        lower, upper = midpoint_bounds(start + mid * delta, diameter)
        bound = lower - speed * (hi - lo) / 2 - RESERVE_MM
        if bound >= -allowance:
            lower_bounds.append(bound)
        elif upper + RESERVE_MM < -allowance:
            return bound, {"status": "overlap", "time": mid, "upper_mm": upper}
        elif depth == max_depth:
            return bound, {"status": "unresolved", "interval": [lo, hi]}
        else:
            pending.extend([(mid, hi, depth + 1), (lo, mid, depth + 1)])
    return min(lower_bounds), None


def evaluate(poses, rest, radius_mm=0.3, allowance_mm=0.01, max_depth=10):
    """Evaluate the original nonlocal material-pair registry over every interval."""
    poses = np.asarray(poses, dtype=float)
    rest = np.asarray(rest, dtype=float)
    if (poses.ndim != 3 or poses.shape[-1] != 3 or len(poses) < 2
            or rest.shape != (poses.shape[1] - 1,) or np.any(rest <= 0) or np.any(rest > 10000)
            or not np.isfinite(rest).all() or not np.isfinite(poses).all()
            or np.max(np.abs(poses), initial=0) > 10000
            or not np.isfinite([radius_mm, allowance_mm]).all()
            or not 0 <= allowance_mm < 2 * radius_mm or radius_mm > 10000
            or not isinstance(max_depth, int) or not 0 <= max_depth <= 20):
        raise ValueError("Expected finite millimetre poses, positive material lengths and valid tolerances")
    left, right = self_pairs(rest, radius_mm)
    if not len(left):
        raise ValueError("The supplied material has no nonlocal segment pairs")
    diameter = 2 * radius_mm
    failures = []
    worst = None
    for frame, (start, finish) in enumerate(zip(poses[:-1], poses[1:])):
        low = np.minimum.reduce([start[:-1], start[1:], finish[:-1], finish[1:]])
        high = np.maximum.reduce([start[:-1], start[1:], finish[:-1], finish[1:]])
        separation = np.maximum(0, np.maximum(low[left]-high[right], low[right]-high[left]))
        bounds = np.linalg.norm(separation, axis=1) - diameter - RESERVE_MM
        for match in np.flatnonzero(bounds < -allowance_mm):
            i, j = int(left[match]), int(right[match])
            indices = [i, i+1, j, j+1]
            bounds[match], failure = narrow_interval(
                start[indices], finish[indices], diameter, allowance_mm, max_depth
            )
            if failure is not None:
                failures.append({"frame": frame, "edges": [i, j], **failure})
        index = int(np.argmin(bounds))
        row = {"frame": frame, "edges": [int(left[index]), int(right[index])],
               "lower_mm": float(bounds[index])}
        if worst is None or row["lower_mm"] < worst["lower_mm"]:
            worst = row
    return {"intervals": len(poses)-1, "pairs_per_interval": len(left),
            "pair_intervals": len(left) * (len(poses)-1),
            "allowance_mm": allowance_mm, "worst": worst,
            "failures": failures, "passed": not failures}


def coil_example():
    """Create a two-turn 6 mm radius helix and open its pitch uniformly."""
    theta = np.linspace(0.0, 4.0 * np.pi, 129)
    poses = np.array([
        np.column_stack([6.0 * np.cos(theta), 6.0 * np.sin(theta),
                         pitch * theta / (2.0 * np.pi)])
        for pitch in np.linspace(1.2, 2.2, 9)
    ])
    return poses, np.linalg.norm(np.diff(poses[0], axis=0), axis=1)


if __name__ == "__main__":
    result = evaluate(*coil_example())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
