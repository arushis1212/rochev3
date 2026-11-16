"""Finite candidate hook/slider and paired physical stripper contacts."""
import numpy as np
from physics.roche_contact3d import HookContact,extrusion_distance

class TransferContact:
    def __init__(self,profiles,advance,gate,plates=True,lift_mm=0.):
        self.profiles=profiles;self.advance=advance;self.hook=HookContact(profiles,gate);self.plates=plates;self.lift_mm=lift_mm
    def components(self,p):
        local=p.copy();local[:,0]-=self.advance;parts=self.hook.components(local)
        if self.plates:
            parts += [extrusion_distance(p,self.profiles[name]) for name in ['R01_front_stripper','R02_rear_stripper']]
        for name in ['R03_lift_pin_0','R03_lift_pin_1']:
            if name in self.profiles:
                local=p.copy();local[:,1]-=self.lift_mm;parts.append(extrusion_distance(local,self.profiles[name]))
        return parts
    def distance(self,p):
        parts=self.components(p);d,g=parts[0]
        for x,n in parts[1:]:
            mask=x<d;d[mask]=x[mask];g[mask]=n[mask]
        return d,g

def crossings(q):
    rows=[]
    for a,b in zip(q[:-1],q[1:]):
        if (a[2]<=0<b[2]) or (b[2]<=0<a[2]):rows.append((a+(b-a)*(-a[2]/(b[2]-a[2]))).tolist())
    return rows

def transfer_metrics(q,advance,gate,cfg,tool,radius):
    local=q.copy();local[:,0]-=advance
    cross=crossings(local);near=[p for p in cross if abs(p[1])<10]
    # Necessary finite-radius inequalities. Do not infer connected-loop topology.
    on_shaft=bool(near and all(p[0]+radius<=cfg['heel_start_u'] and p[0]-radius>=tool['barrel_front'] and p[1]-radius>=tool['body_top']-.01 for p in near))
    over_gate=bool(on_shaft and all(p[1]-radius>=tool['gate_bottom']+tool['gate_thickness']-.01 for p in near))
    cleared=bool(near and all(p[0]-radius>=tool['body_tip'] for p in near))
    return {'midplane_crossings_uvw_mm':cross,'finite_radius_crossing_on_shaft':on_shaft,'finite_radius_crossing_over_gate':over_gate,'finite_radius_crossing_clear_of_nose':cleared}
