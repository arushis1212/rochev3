"""Replay the fork withdrawal coordinate and calculate the minimum two-pin loop perimeter."""
import json
from pathlib import Path

import numpy as np


DATA=Path(__file__).resolve().parents[1]/'cad/castoff/geometry.json'


def crossings(material,frame):
    points=np.asarray(material,dtype=float)
    origin=np.asarray(frame['point'])
    axial=np.asarray(frame['axis'])
    transverse=np.asarray(frame['toward_second'])
    normal=np.cross(axial,transverse)
    if (abs(np.linalg.norm(axial)-1)>1e-8 or abs(np.linalg.norm(transverse)-1)>1e-8
            or abs(axial@transverse)>1e-8 or np.any(np.diff(points[:,0])<=0)):
        raise ValueError('Expected orthonormal fork axes and increasing material coordinates')
    events=[]
    for a,b in zip(points,points[1:]):
        da=(a[1:]-origin)@normal
        dn=(b[1:]-a[1:])@normal
        if abs(dn)<1e-10:
            if abs(da)<1e-10:
                raise ValueError('Coplanar yarn segment requires an additional intersection test')
            continue
        fraction=-da/dn
        if not 0<=fraction<1:
            continue
        mark,*xyz=a+(b-a)*fraction
        local=xyz-origin
        height=local@axial
        width=local@transverse
        if frame['near']<height<frame['far'] and 0<width<frame['separation']:
            withdrawal=frame['far']-height
            if 0<=withdrawal<=frame['stroke']:
                events.append(dict(withdrawal_mm=float(withdrawal),mark_mm=float(mark),
                                   orientation=int(np.sign(dn))))
    return events


def replay(path=DATA):
    data=json.loads(Path(path).read_text())
    events=[]
    for name,material in data['retained'].items():
        events.extend(dict(loop=name,**hit) for hit in crossings(material,data['frame']))
    tips=np.asarray(data['pin_tips_xyz_mm'])
    spacing=np.linalg.norm(tips[1]-tips[0])
    radius=data['pin_radius_mm']+data['yarn_radius_mm']+data['position_allowance_mm']
    loop=np.asarray(data['exposed_live_bight'])[:,1:]
    arc=np.linalg.norm(np.diff(loop,axis=0),axis=1).sum()
    neck=np.linalg.norm(loop[-1]-loop[0])
    # Convex hull of the two inflated circular pin cross-sections is a stadium.
    required=2*spacing+2*np.pi*radius
    return dict(releases=sorted(events,key=lambda x:x['withdrawal_mm']),stroke_mm=data['frame']['stroke'],
                pin_spacing_mm=float(spacing),required_loop_width_mm=float(spacing+2*radius),
                minimum_loop_perimeter_mm=float(required),sampled_bight_with_neck_chord_mm=float(arc+neck))


if __name__=='__main__':
    print(json.dumps(replay(),indent=2))
