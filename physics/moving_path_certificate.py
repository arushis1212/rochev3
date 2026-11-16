"""Adaptive Lipschitz certificate for interpolated yarn and translating solids."""
import numpy as np
from physics.roche_contact3d import gap_bound,self_contact,self_pairs

def certify_moving_path(a,b,state0,state1,rest,radius,obstacle_factory,max_subdivisions=32):
    a=np.asarray(a);b=np.asarray(b);s0=np.asarray(state0);s1=np.asarray(state1)
    motion=float(np.max(np.linalg.norm(b-a,axis=1)));delta=s1-s0;du,dg,dh=delta[:3];dr=delta[3] if len(delta)>3 else 0.
    rigid=float(max(abs(du),abs(du-dg),np.hypot(dh,dr)));pairs=self_pairs(rest,radius);cache={}
    def sample(t):
        if t not in cache:
            q=(1-t)*a+t*b;ob=obstacle_factory((1-t)*s0+t*s1)
            g=gap_bound(q,radius,ob,spacing=.002,chord_error=0)
            cache[t]=(g['polyline_gap_lower_bound_mm']+radius,self_contact(q,rest,radius,1.,pairs)[2]+2*radius,g['sampled_surface_gap_mm']+radius)
        return cache[t]
    n=1
    while True:
        values=[sample(float(t))for t in np.linspace(0,1,n+1)]
        solid=min(v[0]for v in values)-(motion+rigid)/(2*n)
        strand=min(v[1]for v in values)-motion/n
        result={'solid_centerline_bound_mm':float(solid),'nonlocal_centerline_bound_mm':float(strand),'max_node_motion_mm':motion,'max_rigid_motion_mm':rigid,'subdivisions':n,'samples_evaluated':len(cache),'certified':bool(solid>0 and strand>0),'finite_tube_gap_bound_mm':float(solid-radius),'scope':'Linear interpolation centerline noncrossing, not dynamic stability or continuous finite-tube clearance.'}
        if result['certified'] or n>=max_subdivisions or min(v[2]for v in values)<0 or min(v[1]for v in values)<=0:return result
        n*=2
