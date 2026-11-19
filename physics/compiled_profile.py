"""Compiled Euclidean line/arc distance; identical half-open ray convention.

No fastmath, parallel reduction or geometric approximation is used. Prepared
profiles are private deep copies, so caller edits cannot invalidate cached data.
"""
import copy
import numpy as np
from numba import njit

def prepare_wire(wire):
    w=copy.deepcopy(wire)
    features=w.get('analytic_features')
    if features is None:
        p=np.asarray(w['points']);features=[{'kind':'LINE','a':a,'b':b}for a,b in zip(p,np.roll(p,-1,axis=0))]
    rows=[]
    for f in features:
        row=np.zeros(15);row[1:3]=f['a'];row[3:5]=f['b']
        if f['kind']=='CIRCLE':
            row[0]=1;row[5:7]=f['center'];row[7:10]=[f['radius'],f['start_angle'],f['sweep']]
            cuts=[0.,1.]
            for a in [np.pi/2,3*np.pi/2]:
                t=((a-row[8])*np.sign(row[9])%(2*np.pi))/abs(row[9])
                if 1e-12<t<1-1e-12:cuts.append(t)
            cuts.sort();row[10]=len(cuts);row[11:11+len(cuts)]=cuts
        elif f['kind']!='LINE':raise ValueError('Only exact lines/circles are supported')
        rows.append(row)
    w['_compiled_features']=np.asarray(rows,dtype=float);return w

def prepare_profile(profile):
    p=copy.deepcopy(profile);p['outer']=prepare_wire(p['outer']);p['holes']=[prepare_wire(w)for w in p['holes']]
    return p

@njit(cache=True,fastmath=False)
def compiled_wire_distance(points,features):
    distance=np.empty(len(points));normal=np.zeros_like(points);tau=2*np.pi
    for i in range(len(points)):
        x,y=points[i];best=np.inf;nx=0.;ny=0.;crossings=0
        for f in features:
            ax,ay,bx,by=f[1:5]
            if f[0]==0:
                ex=bx-ax;ey=by-ay;t=max(0.,min(1.,((x-ax)*ex+(y-ay)*ey)/(ex*ex+ey*ey)))
                dx=x-ax-t*ex;dy=y-ay-t*ey
                if abs(ey)>1e-14 and (ay>y)!=(by>y) and x<ax+(y-ay)*ex/ey:crossings+=1
            else:
                cx,cy,R,start,sweep=f[5:10];vx=x-cx;vy=y-cy;direction=1. if sweep>0 else -1.
                inside=(((np.arctan2(vy,vx)-start)*direction)%tau)/abs(sweep)<=1+1e-12
                if inside:
                    norm=np.sqrt(vx*vx+vy*vy)
                    if norm<1e-30:dx=x-(cx+R);dy=y-cy
                    else:dx=x-(cx+vx/norm*R);dy=y-(cy+vy/norm*R)
                elif (x-ax)**2+(y-ay)**2<=(x-bx)**2+(y-by)**2:dx=x-ax;dy=y-ay
                else:dx=x-bx;dy=y-by
                zray=np.round((y-cy)/R,14);alpha=np.arcsin(max(-1.,min(1.,zray)))
                for j in range(int(f[10])-1):
                    sa=start+f[11+j]*sweep;sb=start+f[12+j]*sweep
                    ya=np.round(np.sin(sa),14);yb=np.round(np.sin(sb),14)
                    if (ya>zray)!=(yb>zray) and abs(zray)<1:
                        for theta in [alpha,np.pi-alpha]:
                            sg=1. if sb-sa>0 else -1.;t=(((theta-sa)*sg)%tau)/abs(sb-sa)
                            if t<=1+1e-12 and x<cx+R*np.cos(theta):crossings+=1
            d=np.sqrt(dx*dx+dy*dy)
            if d<best:best=d;nx=dx/max(d,1e-30);ny=dy/max(d,1e-30)
        sign=-1. if crossings%2 else 1.;distance[i]=sign*best;normal[i,0]=sign*nx;normal[i,1]=sign*ny
    return distance,normal
