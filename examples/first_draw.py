"""Replay two dyed yarn marks as the closed crochet hook draws a bight."""
import json
from pathlib import Path

import numpy as np

from physics.full_stitch_aperture import _point_segment, _segment_triangle
from physics.loop_holding import head_frame


MOTION = Path(__file__).with_name("first_draw_motion.npz")
SECTIONS_MM = (-1.1128, -.8128, 0., .8128, 1.1128)
HEEL = (-7.5, -.4, -.6, 1.7)
NOSE = (.4, 3., -.6, 1.7)


def disk_crossings(points, vertices, triangles, parameter, yarn_radius):
    """Intersect a piecewise linear path with the oriented, material-bound disk."""
    faces = vertices[triangles]
    low, high = faces.min(axis=1), faces.max(axis=1)
    events = []
    for i, (a, b) in enumerate(zip(points[:-1], points[1:])):
        if np.array_equal(a, b):
            continue
        candidates = np.all(low <= np.maximum(a, b) + 1e-9, axis=1)
        candidates &= np.all(high >= np.minimum(a, b) - 1e-9, axis=1)
        for triangle in np.flatnonzero(candidates):
            hit = _segment_triangle(a, b, faces[triangle], 1e-9)
            if hit["kind"] in ("coplanar", "degenerate"):
                raise ValueError("The marker trajectory has a non-transverse intersection")
            for fraction, point, barycentric in hit["points"]:
                if np.min(barycentric) < 1e-8 or not 1e-9 < fraction < 1-1e-9:
                    raise ValueError("A boundary event requires an explicit shared-face or shared-step check")
                rim = min(_point_segment(point, p, q) for p, q in zip(vertices[:-1], vertices[1:]))
                events.append(dict(step=i+1, sign=hit["sign"],
                                   parameter_mm=float(parameter[i] + fraction*(parameter[i+1]-parameter[i])),
                                   physical_rim_surface_gap_mm=rim - 2*yarn_radius,
                                   diagnostic_neck_distance_mm=_point_segment(point, vertices[-1], vertices[0])))
    return events


def real_times(coefficients):
    poly = np.trim_zeros(np.asarray(coefficients), "b")
    if len(poly) < 2:
        return []
    return [float(z.real) for z in np.roots(poly[::-1])
            if abs(z.imag) < 1e-9 and 0. < z.real < 1.]


def sections_stay_captured(before, after, rect, sign):
    """Check each finite pocket section throughout one affine motion interval.

    A moving line cuts the section at a ratio of quadratics to a linear
    denominator. Its membership changes only at a vertex/plane event or when
    that intersection reaches one of the four section boundaries.
    """
    margin = 1e-9
    lower = np.minimum.reduce([before[:-1], before[1:], after[:-1], after[1:]])
    upper = np.maximum.reduce([before[:-1], before[1:], after[:-1], after[1:]])
    in_rectangle = ((lower[:, 0] <= rect[1]+margin) & (upper[:, 0] >= rect[0]-margin)
                    & (lower[:, 1] <= rect[3]+margin) & (upper[:, 1] >= rect[2]-margin))
    for plane in SECTIONS_MM:
        edges = np.flatnonzero(in_rectangle & (lower[:, 2] <= plane+margin) & (upper[:, 2] >= plane-margin))
        times = [0., 1.]
        for i in edges:
            a = np.column_stack((before[i], after[i]-before[i]))
            b = np.column_stack((before[i+1], after[i+1]-before[i+1]))
            a[2, 0] -= plane
            b[2, 0] -= plane
            if np.max(np.abs([*a[2], *b[2]])) < 1e-12:
                return False
            times.extend(real_times(a[2]))
            times.extend(real_times(b[2]))
            denominator = b[2]-a[2]
            for axis, bounds in enumerate((rect[:2], rect[2:])):
                numerator = np.convolve(a[axis], b[2])-np.convolve(b[axis], a[2])
                for bound in bounds:
                    times.extend(real_times(numerator - bound*np.r_[denominator, 0.]))
        times = np.unique(times)
        for t in np.r_[times, .5*(times[:-1]+times[1:])]:
            a = before[edges] + t*(after[edges]-before[edges])
            b = before[edges+1] + t*(after[edges+1]-before[edges+1])
            za, zb = a[:, 2]-plane, b[:, 2]-plane
            cross = ((za <= 0) & (zb > 0)) | ((zb <= 0) & (za > 0))
            u = -za[cross]/(zb[cross]-za[cross])
            xy = a[cross, :2] + u[:, None]*(b[cross, :2]-a[cross, :2])
            inside = ((rect[0] <= xy[:, 0]) & (xy[:, 0] <= rect[1]) &
                      (rect[2] <= xy[:, 1]) & (xy[:, 1] <= rect[3]))
            if np.sign((zb-za)[cross][inside]).tolist() != [sign]:
                return False
    return True


def replay(file=MOTION):
    with np.load(file, allow_pickle=False) as data:
        s = data["material_s_mm"]
        heads = data["head_tip_mm"]
        frames = np.repeat(data["start_xyz_mm"][None, :, :], len(heads), axis=0)
        frames[:, data["moving_indices"]] = data["moving_xyz_mm"]
        vertices, triangles = data["aperture_vertices_mm"], data["aperture_triangles"]
        radius = float(data["yarn_radius_mm"])
        split = data["loop_and_working_boundary_s_mm"][1]
        inclination, roll = map(float, (data["head_inclination_deg"], data["head_roll_deg"]))
    if np.any(np.diff(s) <= 0) or not np.all(np.isfinite(frames)):
        raise ValueError("The material coordinates must be finite and strictly ordered")
    arcs = np.r_[0., np.cumsum(np.linalg.norm(np.diff(heads, axis=0), axis=1))]
    labels = {}
    for name, mark in (("cloth_limb", 1024.), ("supply_limb", 1040.)):
        i = np.searchsorted(s, mark) - 1
        t = (mark-s[i])/(s[i+1]-s[i])
        pts = frames[:, i, :] + t*(frames[:, i+1, :]-frames[:, i, :])
        events = disk_crossings(pts, vertices, triangles, arcs, radius)
        for event in events:
            event["hook_travel_mm"] = event.pop("parameter_mm")
        labels[name] = dict(material_s_mm=mark, events=events,
            net_oriented_crossings=sum(r["sign"] for r in events),
            final_whole_fiber_forward_margin_mm=float(vertices[:, 1].min()-pts[-1, 1]-2*radius))
    local = []
    for q, tip in zip(frames, heads):
        origin, rotation = head_frame(tip, angle=inclination, roll=roll)
        local.append((q-origin) @ rotation)
    retained = {}
    for name, use, rect, direction in (("old_heel", s <= split+1e-8, HEEL, -1),
                                        ("working_nose", s >= split-1e-8, NOSE, 1)):
        retained[name] = all(sections_stay_captured(a[use], b[use], rect, direction)
                             for a, b in zip(local[:-1], local[1:]))
    bounds = []
    working = s >= split-1e-8
    for geometry in (frames[0], frames[-1]):
        hits = disk_crossings(geometry[working], vertices, triangles, s[working], radius)
        if [x["sign"] for x in hits] != [-1, 1]:
            raise ValueError("The working fold has lost its oriented opening")
        bounds.append([x["parameter_mm"] for x in hits])
    rest_gain = (bounds[1][1]-bounds[1][0]) - (bounds[0][1]-bounds[0][0])
    return dict(motion_intervals=len(heads)-1, hook_travel_mm=float(arcs[-1]),
                yarn_diameter_mm=2*radius, fixed_mark_traces=labels,
                initial_and_final_bight_material_bounds_mm=bounds, bight_rest_gain_mm=rest_gain,
                retained_through_all_five_pocket_sections=retained)


if __name__ == "__main__":
    print(json.dumps(replay(), indent=2, allow_nan=False))
