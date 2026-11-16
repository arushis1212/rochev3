"""Euclidean distance and ray parity for exact planar line/circular-arc wires."""
import numpy as np

TAU=2*np.pi

def parameter(angle,start,sweep):
    return np.mod((angle-start)*np.sign(sweep),TAU)/abs(sweep)


def wire_distance(points,wire):
    if 'analytic_features' not in wire:
        # Test fixtures can still supply exact linear polygons.
        a=np.asarray(wire['points']);features=[{'kind':'LINE','a':x,'b':y} for x,y in zip(a,np.roll(a,-1,axis=0))]
    else:features=wire['analytic_features']
    p=np.asarray(points);best=np.full(len(p),np.inf);normal=np.zeros_like(p);crossings=np.zeros(len(p),dtype=int)
    for f in features:
        a=np.asarray(f['a']);b=np.asarray(f['b'])
        if f['kind']=='LINE':
            e=b-a;t=np.clip((p-a)@e/np.dot(e,e),0,1);delta=p-a-t[:,None]*e
            crosses=(a[1]>p[:,1])!=(b[1]>p[:,1])
            if abs(e[1])>1e-14:crossings+=crosses & (p[:,0]<a[0]+(p[:,1]-a[1])*e[0]/e[1])
        elif f['kind']=='CIRCLE':
            c=np.asarray(f['center']);R=f['radius'];start=f['start_angle'];sweep=f['sweep'];v=p-c
            angle=np.arctan2(v[:,1],v[:,0]);inside=parameter(angle,start,sweep)<=1+1e-12
            norm=np.linalg.norm(v,axis=1);radial=v/np.maximum(norm[:,None],1e-30)*R
            radial[norm<1e-30]=[R,0.]
            da=p-a;db=p-b;closest=np.where((np.sum(da*da,axis=1)<=np.sum(db*db,axis=1))[:,None],a,b)
            closest[inside]=c+radial[inside];delta=p-closest
            # Split at y extrema. Each monotone arc then uses the same half-open
            # lower/upper ray convention as a line, including shared vertices.
            cuts=[0.,1.]
            for extrema in (np.pi/2,3*np.pi/2):
                t=float(parameter(extrema,start,sweep))
                if 1e-12<t<1-1e-12:cuts.append(t)
            cuts.sort()
            z=(p[:,1]-c[1])/R;zray=np.round(z,14);alpha=np.arcsin(np.clip(zray,-1,1))
            for lo,hi in zip(cuts[:-1],cuts[1:]):
                sa=start+lo*sweep;sb=start+hi*sweep;ya=np.round(np.sin(sa),14);yb=np.round(np.sin(sb),14)
                crosses=((ya>zray)!=(yb>zray)) & (abs(zray)<1)
                for theta in (alpha,np.pi-alpha):
                    t=parameter(theta,sa,sb-sa)
                    valid=(t<=1+1e-12)&crosses
                    crossings+=valid & (p[:,0]<c[0]+R*np.cos(theta))
        else:raise ValueError('Only exact lines/circles are supported')
        distance=np.linalg.norm(delta,axis=1);use=distance<best
        best[use]=distance[use];normal[use]=delta[use]/np.maximum(distance[use,None],1e-30)
    sign=np.where(crossings%2,-1.,1.)
    return best*sign,normal*sign[:,None]
