"""Measure the straight receiver corridor through both registered yarn bights."""
from pathlib import Path

import numpy as np


def segment_distance(a, b, c, d):
    """Minimum length of the connector between two closed, finite segments."""
    u, v = b-a, d-c
    w = a-c
    uu, vv, uv = u@u, v@v, u@v
    if min(uu, vv) == 0:
        raise ValueError("A polyline segment must have positive length")
    uw, vw = u@w, v@w
    candidates = [(0., np.clip(vw/vv, 0., 1.)), (1., np.clip((vw+uv)/vv, 0., 1.)),
                  (np.clip(-uw/uu, 0., 1.), 0.), (np.clip((uv-uw)/uu, 0., 1.), 1.)]
    det = uu*vv - uv*uv
    if det > 1.e-14*uu*vv:
        s, t = (uv*vw-vv*uw)/det, (uu*vw-uv*uw)/det
        if 0. < s < 1. and 0. < t < 1.:
            candidates.append((s,t))
    return min(np.linalg.norm(w+s*u-t*v) for s,t in candidates)


def crossings(start, end, bight):
    """Return the signed intersections with a triangle fan spanning the bight and its neck chord."""
    delta = end-start
    length = np.linalg.norm(delta)
    if length == 0:
        raise ValueError("A probe stroke must have positive length")
    found = []
    for b,c in zip(bight[1:-1], bight[2:]):
        # Invert p + t*delta = a + u*(b-a) + v*(c-a).
        a = bight[0]
        mat = np.column_stack((delta, a-b, a-c))
        if abs(np.linalg.det(mat)) < 1.e-9:
            continue
        t,u,v = np.linalg.solve(mat, a-start)
        if 0. < t < 1. and 0. < u and 0. < v and u+v < 1.:
            found.append((float(t*length), int(np.sign(delta @ np.cross(b-a,c-a)))))
    return sorted(found)


def threaded_material(yarn, labels, rectangle):
    """Locate physical yarn crossing the planar fork opening using its two orthogonal edges."""
    origin=rectangle[0]
    u,v=rectangle[1]-origin, rectangle[3]-origin
    normal=np.cross(u,v)
    events=[]
    for j,(a,b) in enumerate(zip(yarn,yarn[1:])):
        projection=(b-a)@normal
        if abs(projection)<1.e-12:
            continue
        t=((origin-a)@normal)/projection
        q=a+t*(b-a)-origin
        if 0.<=t<1. and 0.<q@u<u@u and 0.<q@v<v@v:
            events.append((float(labels[j]+t*(labels[j+1]-labels[j])),int(np.sign(projection))))
    return events


def measure():
    with np.load(Path(__file__).with_suffix('.npz'), allow_pickle=False) as data:
        start, end = data['start_xyz_mm'], data['end_xyz_mm']
        yarn = data['yarn_xyz_mm']
        distance = min(segment_distance(start,end,c,d) for c,d in zip(yarn,yarn[1:]))
        return dict(old_material=threaded_material(data['old_bight_xyz_mm'], data['old_marks_mm'], data['receiver_face_mm']),
                    drawn_material=threaded_material(data['drawn_bight_xyz_mm'], data['drawn_marks_mm'], data['receiver_face_mm']),
                    old=crossings(start,end,data['old_bight_xyz_mm']),
                    drawn=crossings(start,end,data['drawn_bight_xyz_mm']),
                    yarn_skin_gap_mm=float(distance-data['probe_radius_mm']-data['yarn_radius_mm']),
                    hardware_gap_mm=float(data['installed_axis_gap_mm']-data['probe_radius_mm']),
                    stroke_mm=float(np.linalg.norm(end-start)), yarn_segments=len(yarn)-1)


if __name__=='__main__':
    result=measure()
    for key in ('old','drawn'):
        print(f"{key:5} bight intersections at {result[key]} (mm, orientation)")
    print(f"Material through fork (mm, orientation) {result['old_material']} and {result['drawn_material']}")
    print(f"Probe to yarn     {result['yarn_skin_gap_mm']:.6f} mm")
    print(f"Probe to hardware {result['hardware_gap_mm']:.6f} mm")
