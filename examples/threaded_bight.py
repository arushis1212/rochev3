"""Measure the two fresh limbs through two material-bounded disks at a posed draw endpoint."""
import json
from pathlib import Path

import numpy as np
from physics.full_stitch_aperture import MaterialAperture


def measure(path=None):
    with np.load(path or Path(__file__).with_suffix('.npz'), allow_pickle=False) as data:
        q, s = data['q_mm'], data['s_mm']
        local = (q - data['eye_origin_mm']) @ data['eye_basis']
        center = []
        for i in np.flatnonzero((local[:-1, 2] < 0.) & (local[1:, 2] >= 0.)):
            fraction = -local[i, 2] / (local[i+1, 2]-local[i, 2])
            u, v = (local[i]+fraction*(local[i+1]-local[i]))[:2]
            if 1.04 < u < 2.36 and -.31 < v < 1.70:
                center.append(float(s[i]+fraction*(s[i+1]-s[i])))
        if len(center) != 1:
            raise ValueError('Need one fresh strand at the middle of the closed eye')
        fresh_start = float(data['fresh_start_mm'])
        if center[0] <= fresh_start:
            raise ValueError('Eye contains material from the held loops')
        loops = {}
        for name in ('L0','L1'):
            marks = data[name+'_material_mm']
            triangles = data[name+'_triangles']
            ring = np.column_stack([np.interp(marks, s, axis) for axis in q.T])
            normal = np.cross(ring-ring.mean(axis=0), np.roll(ring,-1,axis=0)-ring.mean(axis=0)).sum(axis=0)
            disk = MaterialAperture(marks, triangles, normal)
            crossing = disk.evaluate(q, s, [fresh_start, s[-1]])
            hits = crossing['crossings']
            loops[name] = dict(
                marks_mm=[x['material_s_mm'] for x in hits], signs=[x['sign'] for x in hits],
                two_limbs=bool(crossing['witness_valid'] and len(hits)==2
                    and hits[0]['sign'] == -hits[1]['sign']
                    and hits[0]['material_s_mm'] < center[0] < hits[1]['material_s_mm']))
        return dict(eye_center_material_mm=center[0],loops=loops)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path)
    print(json.dumps(measure(parser.parse_args().data), indent=2))
