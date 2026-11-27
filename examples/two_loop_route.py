"""Locate a compact closed tool's crossings through two registered, stationary loops."""
import json
from pathlib import Path
import numpy as np
from physics.full_stitch_aperture import _segment_triangle, surface_validation


def measure(path=None):
    with np.load(path or Path(__file__).with_suffix('.npz'), allow_pickle=False) as data:
        path=data['reference_mm']
        events=[]
        for name in ('L0','L1'):
            boundary=data[name+'_vertices_mm']
            triangles=data[name+'_triangles']
            if not surface_validation(boundary,triangles)['valid']:
                raise ValueError('Invalid loop aperture')
            for i,(a,b) in enumerate(zip(path,path[1:])):
                for face in boundary[triangles]:
                    r=_segment_triangle(a,b,face,1e-8)
                    for progress,point,_ in r['points']:
                        events.append(dict(loop=name,leg=i,leg_fraction=float(progress),
                                           sign=int(r['sign']),position_mm=point.tolist()))
        return dict(translation_legs=len(path)-1,crossings=sorted(events,key=lambda e:(e['leg'],e['leg_fraction'])))


if __name__=='__main__':
    print(json.dumps(measure(),indent=2))
