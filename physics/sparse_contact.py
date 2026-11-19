"""Sparse exact active penalties; expanded AABBs discard only zero energy terms."""
import numpy as np
from physics.roche_contact3d import extrusion_bounds,extrusion_distance

def active_indices(points,lo,hi,radius):
    return np.flatnonzero(np.all((points>=lo-radius)&(points<=hi+radius),axis=1))

def profile_term(points,profile,radius,shift=(0,0,0)):
    shift=np.asarray(shift);lo,hi=extrusion_bounds(profile);idx=active_indices(points,lo+shift,hi+shift,radius)
    if len(idx):
        d,g=extrusion_distance(points[idx]-shift,profile);yield idx,d,g

def world_terms(world,points,radius):
    local=(points-world.origin)@world.frame;t=world.local
    items=[('H01_hook_body',[t.advance,0,0]),('H02_gate',[t.advance-t.hook.gate_displacement,0,0])]
    if t.plates:items += [(n,[0,0,0]) for n in ['R01_front_stripper','R02_rear_stripper']]
    items += [(n,[t.reset_mm,t.lift_mm,0]) for n in ['R03_lift_pin_0','R03_lift_pin_1'] if n in t.profiles]
    for name,shift in items:
        for idx,d,g in profile_term(local,t.profiles[name],radius,shift):yield idx,d,g@world.frame.T
    aux=world.auxiliary
    for spec in aux.envelopes.values():
        lo,hi=aux.bounds(spec);idx=active_indices(local,lo,hi,radius)
        if len(idx):
            d,g=aux.shape_distance(local[idx],spec);yield idx,d,g@world.frame.T
    yield from profile_term(points,world.baseprofiles['B06_knockover'],radius)
