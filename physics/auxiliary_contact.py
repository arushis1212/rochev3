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
    def __init__(self,envelopes,lift=0.):self.envelopes=envelopes;self.lift=lift
    def components(self,p):
        result=[]
        for spec in self.envelopes.values():
            b=np.array(spec['bbox_mm']);lo=b[::2].copy();hi=b[1::2].copy()
            if spec['moves_with_lift']:lo[1]+=self.lift;hi[1]+=self.lift
            result.append(box_distance3d(p,lo,hi))
        return result
    def distance(self,p):
        parts=self.components(p);d,g=parts[0]
        for x,n in parts[1:]:
            mask=x<d;d[mask]=x[mask];g[mask]=n[mask]
        return d,g
