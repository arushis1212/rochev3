"""Replay static balance on a registered yarn donor with a floating carriage."""
import json
from pathlib import Path
import numpy as np
from physics.roche_rod import energy_gradient

def score(data,index):
    q,s=data['q_mm'][index],data['s_mm'][index]
    ghosts,labels=data['neighbor_q_mm'][index],data['neighbor_s_mm'][index]
    normal=data['normal_N'][index]
    z=data['height_mm'][index]
    radius=float(data['groove_radius_mm']+data['rod_radius_mm'])
    rest=np.diff(np.r_[labels[0],s,labels[1]])
    _,grad=energy_gradient(np.vstack([ghosts[0],q,ghosts[1]]),rest,float(data['EA_N']),float(data['B_Nmm2']))
    residual=grad[1:-1].copy()
    residual[:,2]+=.5*(rest[:-1]+rest[1:])*data['weight_N_mm']
    carriage=float(data['carriage_weight_N'])
    gaps=[];active_loads=[]
    for pulley,x in enumerate([32.,64.,48.]):
        center=np.array([x,z if pulley==2 else 230.])
        for i in np.flatnonzero(normal[pulley]>0.):
            a=q[i,[0,2]]-center
            v=q[i+1,[0,2]]-q[i,[0,2]]
            t=float(np.clip(-a@v/(v@v),0.,1.))
            r=a+t*v
            unit=r/np.linalg.norm(r)
            force=normal[pulley,i]*np.array([unit[0],0.,unit[1]])
            residual[i]-=(1-t)*force
            residual[i+1]-=t*force
            if pulley==2:carriage+=force[2]
            gaps.append(abs(np.linalg.norm(r)-radius))
            active_loads.append(float(normal[pulley,i]))
    if not np.all(np.diff(s)>0) or np.min(normal)<0 or not active_loads:raise ValueError('Invalid material coordinates or pulley pressures')
    return dict(issued_mm=float(data['issued_mm'][index]),height_mm=float(z),out_mark_mm=float(s[0]),in_mark_mm=float(s[-1]),
        largest_active_gap_mm=float(max(gaps)),free_yarn_residual_N=float(np.max(abs(residual[1:-1]))),carriage_residual_N=abs(carriage))

def replay(path=None):
    with np.load(path or Path(__file__).with_suffix('.npz'),allow_pickle=False) as data:
        return [score(data,i) for i in range(len(data['issued_mm']))]

if __name__=='__main__':print(json.dumps(replay(),indent=2))
