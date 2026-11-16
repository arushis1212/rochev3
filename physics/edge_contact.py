"""Exact fixed-quadrature contact with segment/AABB broad-phase culling."""
import numpy as np
from physics.roche_contact3d import extrusion_bounds,extrusion_distance

def edge_samples(q,rest,counts,lo,hi,radius):
    """Keep original midpoint indices only inside an expanded solid AABB.

    Slab intervals are rounded outward. Discarded sample penalties and gradients
    are identically zero; no adaptive quadrature or material change is introduced.
    """
    lo=np.asarray(lo)-radius;hi=np.asarray(hi)+radius;a=q[:-1];v=np.diff(q,axis=0)
    lower=np.zeros(len(rest));upper=np.ones(len(rest));valid=np.ones(len(rest),dtype=bool)
    for axis in range(3):
        fixed=v[:,axis]==0
        valid &= ~fixed | ((a[:,axis]>=lo[axis])&(a[:,axis]<=hi[axis]))
        den=np.where(fixed,1,v[:,axis]);t0=(lo[axis]-a[:,axis])/den;t1=(hi[axis]-a[:,axis])/den
        lower=np.maximum(lower,np.where(fixed,0,np.minimum(t0,t1)))
        upper=np.minimum(upper,np.where(fixed,1,np.maximum(t0,t1)))
    valid &= lower<=upper
    edges=[];fractions=[]
    for edge in np.flatnonzero(valid):
        n=int(counts[edge]);first=max(0,int(np.ceil(n*lower[edge]-.5-1e-10)));last=min(n-1,int(np.floor(n*upper[edge]-.5+1e-10)))
        if first>last:continue
        t=(np.arange(first,last+1)+.5)/n;edges.extend([edge]*len(t));fractions.extend(t)
    edges=np.asarray(edges,dtype=int);t=np.asarray(fractions)
    return edges,t,rest[edges]/counts[edges],a[edges]+t[:,None]*v[edges]

def profile_edges(q,rest,counts,profile,radius,shift=(0,0,0)):
    shift=np.asarray(shift);lo,hi=extrusion_bounds(profile)
    edge,t,weight,p=edge_samples(q,rest,counts,lo+shift,hi+shift,radius)
    if len(edge):
        d,g=extrusion_distance(p-shift,profile);yield edge,t,weight,d,g

def world_edge_terms(world,q,rest,counts,radius):
    local=(q-world.origin)@world.frame;t=world.local
    items=[('H01_hook_body',[t.advance,0,0]),('H02_gate',[t.advance-t.hook.gate_displacement,0,0])]
    if t.plates:items += [(n,[0,0,0]) for n in ['R01_front_stripper','R02_rear_stripper']]
    items += [(n,[t.reset_mm,t.lift_mm,0]) for n in ['R03_lift_pin_0','R03_lift_pin_1'] if n in t.profiles]
    for name,shift in items:
        for e,f,w,d,g in profile_edges(local,rest,counts,t.profiles[name],radius,shift):yield e,f,w,d,g@world.frame.T
    aux=world.auxiliary
    for spec in aux.envelopes.values():
        lo,hi=aux.bounds(spec);edge,ts,weight,p=edge_samples(local,rest,counts,lo,hi,radius)
        if len(edge):
            d,g=aux.shape_distance(p,spec);yield edge,ts,weight,d,g@world.frame.T
    yield from profile_edges(q,rest,counts,world.baseprofiles['B06_knockover'],radius)
