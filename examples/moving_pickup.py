"""Check the actual moving yarn at five hook sections and the gate's central opening."""
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from scipy.spatial import cKDTree


def throat(data, t, seed, spacing=.012):
    radius = float(data['radius_mm'])
    opening = float(data['opening0_mm'] - data['gate_rate_mm_s']*t)
    u = np.arange(-2., 6.+spacing/2, spacing)
    v = np.arange(-2., 5.+spacing/2, spacing)
    x, y = np.meshgrid(u, v, indexing='ij')
    query = np.column_stack([x.ravel(), y.ravel()])
    hook = cKDTree(data['hook_xy']).query(query)[0]
    gate = cKDTree(data['gate_xy']).query(query + [opening, 0.])[0]
    d = np.minimum(hook, gate).reshape(x.shape)
    cell = np.rint((seed-[u[0], v[0]])/spacing).astype(int)
    half_diag = spacing/np.sqrt(2.)
    def outside(mask, neighbors):
        groups, _ = label(mask, structure=neighbors)
        k = groups[tuple(cell)]
        border = np.r_[groups[0],groups[-1],groups[:,0],groups[:,-1]]
        return bool(k), bool(k and np.any(border == k))
    # Inner bound uses arc-length coverage and face-connected cells. Outer
    # bound uses only boundary sample points and includes corner adjacency.
    safe = d - float(data['arc_bound_mm']) - half_diag > radius
    possible = d + half_diag > radius
    free, escapes = outside(safe, [[0,1,0],[1,1,1],[0,1,0]])
    valid, could_escape = outside(possible, np.ones((3,3),dtype=bool))
    return dict(opening_mm=opening, open_path=free and escapes,
                trapped=free and valid and not could_escape)


def replay(path=None):
    with np.load(path or Path(__file__).with_suffix('.npz'), allow_pickle=False) as d:
        q=d['xyz_mm']; s=d['material_mm']; t=d['t_s']
        if not np.all(np.diff(t)>0) or not np.all(np.diff(s)>0):
            raise ValueError('Expected increasing time and material coordinates')
        xmin,xmax,ymin,ymax=d['window_mm']
        lower=np.inf; upper=-np.inf
        for z in d['section_mm']:
            # Half-open segments give a unique owner to a crossing at a vertex.
            a=q[:,:-1]; direction=np.diff(q,axis=1)
            f=np.divide(z-a[:,:,2],direction[:,:,2],out=np.full(direction.shape[:2],np.nan),
                        where=direction[:,:,2]!=0)
            xy=a[:,:,:2]+f[:,:,None]*direction[:,:,:2]
            inside=(f>=0)&(f<1)&(xy[:,:,0]>=xmin)&(xy[:,:,0]<=xmax)&(xy[:,:,1]>=ymin)&(xy[:,:,1]<=ymax)
            if not np.all(inside.sum(axis=1)==1) or not np.all(direction[:,:,2][inside]>0):
                raise ValueError('A section lost its positive material crossing')
            marks=(s[:-1]+f*np.diff(s))[inside]
            if marks.min()<=float(d['fresh_after_mm']):raise ValueError('Previously held material in pocket')
            lower=min(lower,float(marks.min()));upper=max(upper,float(marks.max()))
            if abs(z)<1e-12: mid=xy[inside]
        first=int(np.searchsorted(t,.00133405488))
        return dict(frames=len(t),end_ms=float(1e3*t[-1]),sections=len(d['section_mm']),
                    material_mm=[lower,upper],at_receiver_contact=throat(d,t[first],mid[first]),
                    terminal=throat(d,t[-1],mid[-1]))


if __name__=='__main__':
    print(json.dumps(replay(),indent=2))
