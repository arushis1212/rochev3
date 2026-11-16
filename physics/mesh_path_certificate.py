"""Adaptive centerline interpolation certificate for two material-matched shapes."""
import numpy as np
from physics.roche_contact3d import gap_bound,self_contact,self_pairs

def certify_interpolation(a,b,rest,radius,obstacle,max_subdivisions=32):
    # Each material point interpolates linearly. For two moving strand points,
    # the relative speed bound is twice the largest single-point displacement.
    motion=float(np.max(np.linalg.norm(b-a,axis=1)));pairs=self_pairs(rest,radius);cache={}
    def sample(t):
        if t not in cache:
            q=(1-t)*a+t*b;gap=gap_bound(q,radius,obstacle,spacing=.01,chord_error=0);sg=self_contact(q,rest,radius,1.,pairs)[2]
            cache[t]=(gap['polyline_gap_lower_bound_mm']+radius,sg+2*radius,gap['sampled_surface_gap_mm']+radius)
        return cache[t]
    n=1
    while True:
        values=[sample(float(t)) for t in np.linspace(0,1,n+1)]
        solid=min(x[0] for x in values)-motion/(2*n);strand=min(x[1] for x in values)-motion/n
        result={'certified_centerline_noncrossing':bool(solid>0 and strand>0),'solid_bound_mm':float(solid),'nonlocal_strand_bound_mm':float(strand),'subdivisions':n,'max_node_displacement_mm':motion,'samples_evaluated':len(cache),'scope':'Centerline topology during linear shape interpolation; not continuous finite-tube clearance or an actual motion command.'}
        if result['certified_centerline_noncrossing'] or n>=max_subdivisions or min(x[2] for x in values)<0 or min(x[1] for x in values)<=0:return result
        n*=2
