"""Measure where the registered grip trajectory passes through the two held loop surfaces."""
import json
from pathlib import Path
import numpy as np
from physics.full_stitch_aperture import _segment_triangle

DATA=Path(__file__).resolve().parents[1]/'cad/castoff/released_curve'

def replay(folder=DATA):
    path=np.asarray(json.loads((folder/'route.json').read_text())['mark_xyz_mm'])
    lengths=np.linalg.norm(np.diff(path,axis=0),axis=1)
    events=[]
    with np.load(folder/'loop_geometry.npz') as data:
        for name in ('L1','L0'):
            ring=data[name+'_xyz_mm']
            edges=np.diff(ring,axis=0)
            triangles=ring[data[name+'_faces']]
            for leg,(a,b) in enumerate(zip(path,path[1:])):
                for face in triangles:
                    result=_segment_triangle(a,b,face,1.e-9)
                    for t,point,_ in result['points']:
                        if result['kind']!='hit':
                            raise ValueError('Path touches a loop surface ambiguously')
                        rel=point-ring[:-1]
                        u=np.clip(np.sum(rel*edges,axis=1)/np.maximum(1.e-16,np.sum(edges**2,axis=1)),0,1)
                        gap=np.min(np.linalg.norm(rel-u[:,None]*edges,axis=1))
                        events.append(dict(loop=name,travel_mm=float(sum(lengths[:leg])+t*lengths[leg]),
                                           distance_to_material_centerline_mm=float(gap)))
    return sorted(events,key=lambda event:event['travel_mm'])

if __name__=='__main__':
    print(json.dumps(replay(),indent=2))
