"""Conservative auxiliary-part envelopes. An active envelope blocks admission."""
import numpy as np

def box_distance3d(points,lo,hi):
    points=np.asarray(points);lo=np.asarray(lo);hi=np.asarray(hi)
    if np.any(hi<=lo):raise ValueError('Box bounds must have positive extent')
    delta=points-(lo+hi)/2;excess=abs(delta)-(hi-lo)/2;outer=np.maximum(excess,0);length=np.linalg.norm(outer,axis=1)
    distance=length+np.minimum(np.max(excess,axis=1),0);normal=np.zeros_like(points);outside=length>1e-14
    normal[outside]=outer[outside]/length[outside,None]*np.sign(delta[outside])
    rows=np.flatnonzero(~outside);axes=np.argmax(excess[rows],axis=1);normal[rows,axes]=np.where(delta[rows,axes]>=0,1.,-1.)
    return distance,normal

class AuxiliaryContact:
    def __init__(self,envelopes,lift=0.,advance=0.,gate=0.,reset=0.):self.reset=reset;self.envelopes=envelopes;self.lift=lift;self.advance=advance;self.gate=gate
    def bounds(self,spec):
        b=np.array(spec['bbox_mm']);lo=b[::2].copy();hi=b[1::2].copy()
        kind=spec.get('motion','lift' if spec.get('moves_with_lift') else 'fixed')
        shift={'fixed':[0,0,0],'lift':[0,self.lift,0],'head':[self.advance,0,0],'gate':[self.advance-self.gate,0,0]}[kind]
        if spec.get('resettable',False):shift[0]+=self.reset
        return lo+shift,hi+shift
    def shape_distance(self,p,spec):
        if not spec.get("boxes_mm"):
            lo,hi=self.bounds(spec);return box_distance3d(p,lo,hi)
        parts=[]
        for box in spec["boxes_mm"]:
            piece={**spec,"bbox_mm":box};lo,hi=self.bounds(piece);parts.append(box_distance3d(p,lo,hi))
        d,g=parts[0]
        for x,n in parts[1:]:
            use=x<d;d[use]=x[use];g[use]=n[use]
        return d,g
    def components(self,p):
        result=[]
        for spec in self.envelopes.values():
            result.append(self.shape_distance(p,spec))
        return result
    def distance(self,p):
        parts=self.components(p);d,g=parts[0]
        for x,n in parts[1:]:
            mask=x<d;d[mask]=x[mask];g[mask]=n[mask]
        return d,g
    def contact_components(self,p,radius):
        result=[]
        for spec in self.envelopes.values():
            lo,hi=self.bounds(spec)
            active=np.all((p>=lo-radius)&(p<=hi+radius),axis=1)
            d=np.full(len(p),radius+1.);g=np.zeros_like(p)
            if np.any(active):d[active],g[active]=self.shape_distance(p[active],spec)
            result.append((d,g))
        return result
