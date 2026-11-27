"""Follow one gripped material point across a moving triangulated loop (mm, s, N)."""
from pathlib import Path
import json
import numpy as np
from physics.full_stitch_aperture import MaterialAperture, _barycentric

def interpolate(q, s, marks):
    return np.column_stack([np.interp(marks, s, axis) for axis in q.T])

def transit(p0, p1, ring0, ring1, faces):
    """Solve signed-volume roots on the affine interval and test face interiors."""
    hits = []
    for face_id, (a, b) in enumerate(zip(ring0[faces], ring1[faces])):
        rel = p0 - a[0]
        velocity = p1 - p0 - (b[0] - a[0])
        e, h = a[1:] - a[0]
        de, dh = b[1:] - b[0] - (a[1:] - a[0])
        n0 = np.cross(e, h)
        n1 = np.cross(de, h) + np.cross(e, dh)
        n2 = np.cross(de, dh)
        coef = [rel @ n0, velocity @ n0 + rel @ n1, velocity @ n1 + rel @ n2, velocity @ n2]
        if max(map(abs, coef)) < 1e-16:
            if (np.minimum(p0,p1) <= np.maximum(a.max(0),b.max(0))+1e-9).all() and (np.maximum(p0,p1) >= np.minimum(a.min(0),b.min(0))-1e-9).all():
                raise ValueError('Marked path may be coplanar with a swept face')
            continue
        for root in np.polynomial.polynomial.polyroots(coef):
            t = float(root.real)
            if abs(root.imag) > 1e-9 or not 0 < t <= 1:
                continue
            bary = _barycentric(p0 + t*(p1-p0), a + t*(b-a))
            if bary is None or min(bary) < -1e-8:
                continue
            if min(bary) <= 1e-8:
                raise ValueError('Crossing coincides with a mesh edge')
            derivative = coef[1] + 2*t*coef[2] + 3*t*t*coef[3]
            hits.append(dict(fraction=t, face=face_id, sign=int(np.sign(derivative)), barycentric=bary.tolist()))
    return hits

def replay(path):
    with np.load(path, allow_pickle=False) as data:
        s, q, times = data['s_mm'], data['q_mm'], data['times_s']
        center = float(data['mark_mm'])
        points = np.array([interpolate(frame,s,[center])[0] for frame in q])
        local = (points-data['eye_origin_mm']) @ data['eye_basis']
        grip_error = np.linalg.norm(local - data['grip_local_mm'],axis=1)
        loops = {}
        for name in ('L0','L1'):
            marks, faces = data[name+'_material_mm'], data[name+'_triangles']
            rings = [interpolate(frame,s,marks) for frame in q]
            events, paired = [], []
            for i, (frame,ring) in enumerate(zip(q,rings)):
                edges = ring-ring.mean(axis=0)
                normal = np.cross(edges,np.roll(edges,-1,axis=0)).sum(axis=0)
                hit = MaterialAperture(marks,faces,normal).evaluate(frame,s,[float(data['fresh_start_mm']),s[-1]])
                crossings = hit['crossings']
                paired.append(bool(hit['witness_valid'] and len(crossings)==2 and crossings[0]['sign']==-crossings[1]['sign']
                                   and crossings[0]['material_s_mm'] < center < crossings[1]['material_s_mm']))
                if i:
                    for event in transit(points[i-1],points[i],rings[i-1],ring,faces):
                        event['time_us'] = 1e6*(times[i-1]+event['fraction']*(times[i]-times[i-1]))
                        events.append(event)
            loops[name] = dict(paired_at_frames=paired, events=events)
        return dict(mark_mm=center, grip_error_mm=float(max(grip_error)), loops=loops,
                    max_reported_dynamic_residual_uN=float(1e6*np.max(data['dynamic_residual_N'][1:])))

if __name__ == '__main__':
    for path in sorted(Path(__file__).parent.glob('receiver_transit_*us.npz')):
        print(path.name, json.dumps(replay(path),indent=2))
