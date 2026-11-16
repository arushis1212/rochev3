"""Finite-radius rod contact with polygonal extrusions from the actual hook CAD.
Units mm,N. Profile chord error is carried by independent distance bounds.
"""
import json
import numpy as np
from physics.roche_rod import energy_gradient
from physics.banded_newton import minimize_banded
from scipy.optimize import minimize
from physics.analytic_profile import wire_distance


def polygon_distance(points,vertices):
    p=np.asarray(points);a=np.asarray(vertices);b=np.roll(a,-1,axis=0);e=b-a
    d=p[:,None,:]-a;f=np.clip(np.einsum('nki,ki->nk',d,e)/np.sum(e*e,axis=1),0,1)
    delta=d-f[:,:,None]*e;ds=np.sum(delta*delta,axis=2);j=np.argmin(ds,axis=1)
    nearest=delta[np.arange(len(p)),j];distance=np.sqrt(ds[np.arange(len(p)),j]);gradient=nearest/np.maximum(distance[:,None],1e-14)
    # Even/odd winding, with horizontal edges contributing no crossings.
    dy=e[:,1];safe=np.where(abs(dy)>1e-14,dy,1.)
    cross=((a[None,:,1]>p[:,None,1])!=(b[None,:,1]>p[:,None,1])) & (p[:,None,0]<a[None,:,0]+(p[:,None,1]-a[None,:,1])*e[None,:,0]/safe)
    sign=np.where(np.sum(cross,axis=1)%2,-1.,1.)
    return sign*distance,gradient*sign[:,None]


def extrusion_distance(p,profile):
    axes=profile['profile_axes'];normal=profile['extrusion_axis']
    d,g=wire_distance(p[:,axes],profile['outer'])
    for hole in profile['holes']:
        h,hg=wire_distance(p[:,axes],hole);mask=-h>d;d[mask]=-h[mask];g[mask]=-hg[mask]
    lo,hi=profile['extrusion_bounds_mm'];offset=p[:,normal]-(lo+hi)/2;dn=abs(offset)-(hi-lo)/2
    both=np.column_stack([d,dn]);pos=np.maximum(both,0);length=np.linalg.norm(pos,axis=1)
    weights=np.zeros_like(both);outside=length>1e-14;weights[outside]=pos[outside]/length[outside,None]
    inside=~outside;weights[np.flatnonzero(inside),np.argmax(both[inside],axis=1)]=1.
    grad=np.zeros_like(p);grad[:,axes]=weights[:,0,None]*g;grad[:,normal]=weights[:,1]*np.where(offset>=0,1.,-1.)
    return length+np.minimum(np.max(both,axis=1),0),grad


class HookContact:
    def __init__(self,profiles,gate_displacement=9.):
        self.profiles=profiles;self.gate_displacement=gate_displacement
    def components(self,p):
        body=extrusion_distance(p,self.profiles['H01_hook_body']);gp=p.copy();gp[:,0]+=self.gate_displacement
        return [body,extrusion_distance(gp,self.profiles['H02_gate'])]
    def distance(self,p):
        (body,bg),(gate,gg)=self.components(p);use=gate<body
        body[use]=gate[use];bg[use]=gg[use]
        return body,bg


def contact_energy3d(q,rest,radius,k,obstacle,samples=8):
    ts=(np.arange(samples)+.5)/samples
    p=(1-ts)[None,:,None]*q[:-1,None,:]+ts[None,:,None]*q[1:,None,:]
    points=p.reshape(-1,3);weights=np.repeat(rest,samples);g=np.zeros_like(q);E=0.
    components=obstacle.components(points) if hasattr(obstacle,'components') else [obstacle.distance(points)]
    for d,n in components:
        depth=np.maximum(radius-d,0)
        E+=.5*k*np.dot(weights*depth,depth)/samples
        gp=(-k*(weights*depth)[:,None]*n/samples).reshape(len(rest),samples,3)
        g[:-1]+=np.sum((1-ts)[None,:,None]*gp,axis=1);g[1:]+=np.sum(ts[None,:,None]*gp,axis=1)
    return float(E),g


def closest_segments(a,b,c,d):
    """Vectorized minimum over interior solution plus all four boundary minima."""
    u=b-a;v=d-c;w=a-c;A=np.sum(u*u,axis=1);B=np.sum(u*v,axis=1);C=np.sum(v*v,axis=1);D=np.sum(u*w,axis=1);E=np.sum(v*w,axis=1);det=A*C-B*B
    safe=np.where(det>1e-20,det,1.)
    s=(B*E-C*D)/safe;t=(A*E-B*D)/safe
    valid=(det>1e-20)&(s>=0)&(s<=1)&(t>=0)&(t<=1)
    ss=np.column_stack([s,np.zeros(len(a)),np.ones(len(a)),np.clip(-D/A,0,1),np.clip((B-D)/A,0,1)])
    tt=np.column_stack([t,np.clip(E/C,0,1),np.clip((E+B)/C,0,1),np.zeros(len(a)),np.ones(len(a))])
    delta=w[:,None,:]+ss[:,:,None]*u[:,None,:]-tt[:,:,None]*v[:,None,:];sq=np.sum(delta*delta,axis=2);sq[~valid,0]=np.inf
    j=np.argmin(sq,axis=1);idx=np.arange(len(a));return np.sqrt(sq[idx,j]),delta[idx,j],ss[idx,j],tt[idx,j]


def self_pairs(rest,radius):
    boundary=np.concatenate([[0.],np.cumsum(rest)]);i,j=np.triu_indices(len(rest),2)
    # Exclude contiguous material within one semicircle; also inspect curvature.
    keep=boundary[j]-boundary[i+1]>np.pi*radius
    return i[keep],j[keep]


def self_contact(q,rest,radius,k,pairs):
    i,j=pairs;g=np.zeros_like(q)
    if len(i)==0:return 0.,g,float('inf')
    distance,delta,s,t=closest_segments(q[i],q[i+1],q[j],q[j+1]);depth=np.maximum(2*radius-distance,0)
    weight=rest[i]*rest[j]/(2*radius);n=delta/np.maximum(distance[:,None],1e-14)
    force=(-k*weight*depth)[:,None]*n
    np.add.at(g,i,(1-s)[:,None]*force);np.add.at(g,i+1,s[:,None]*force)
    np.add.at(g,j,-(1-t)[:,None]*force);np.add.at(g,j+1,-t[:,None]*force)
    return float(.5*k*np.dot(weight,depth*depth)),g,float(np.min(distance)-2*radius)


def solve3d(q,rest,EA,B,radius,obstacle,k=1000.,maxiter=100,samples=8):
    ends=q[[0,-1]].copy();pairs=self_pairs(rest,radius)
    def evaluate(x):
        p=np.vstack([ends[0],x.reshape(-1,3),ends[1]])
        E,g=energy_gradient(p,rest,EA,B);C,h=contact_energy3d(p,rest,radius,k,obstacle,samples)
        S,j,_=self_contact(p,rest,radius,k,pairs)
        return E+C+S,(g+h+j)[1:-1].ravel()
    def bandwidth(x):
        p=np.vstack([ends[0],x.reshape(-1,3),ends[1]])
        gap=self_contact(p,rest,radius,k,pairs)[2]
        # Under a colored Hessian perturbation each point moves at most sqrt(3)h;
        # two closest points move at most2sqrt(3)h. Beyond4h the entire
        # self-contact Hessian is exactly zero. Otherwise retain FULL bandwidth.
        return 8 if gap>4e-5 else len(x)-1
    # BFGS provides a different descent metric near changing closest features.
    # Do not accept its status/energy tolerance as a force-equilibrium certificate.
    start=q[1:-1].ravel();initial_energy=evaluate(start)[0]
    result=minimize(evaluate,start,method='BFGS',jac=True,options={'gtol':1e-8,'maxiter':2000})
    x=result.x;final_energy,gradient=evaluate(x);residual=float(np.max(np.abs(gradient)))
    info={'optimizer_success':residual<=1e-7,'message':str(result.message),'iterations':int(result.nit),'energy_Nmm':float(final_energy),'free_node_residual_N':residual,'method':'BFGS_with_force_residual_acceptance','initial_energy_Nmm':float(initial_energy)}
    if residual>1e-7:
        x,refine=minimize_banded(evaluate,x,bandwidth=bandwidth,maxiter=maxiter,step=1e-6)
        info={'BFGS':info,**refine,'method':'BFGS_then_safeguarded_Newton'}
    p=np.vstack([ends[0],x.reshape(-1,3),ends[1]])
    info['self_contact_gap_mm']=self_contact(p,rest,radius,k,pairs)[2]
    return p,info


def gap_bound(q,radius,obstacle,spacing=.01,chord_error=.001):
    lower=float('inf');sample=float('inf')
    for a,b in zip(q[:-1],q[1:]):
        length=np.linalg.norm(b-a);n=max(1,int(np.ceil(length/spacing)))
        d,_=obstacle.distance(a+(b-a)*np.linspace(0,1,n+1)[:,None]);m=float(np.min(d))-radius
        sample=min(sample,m);lower=min(lower,m-length/(2*n)-chord_error)
    return {'sampled_surface_gap_mm':sample,'polyline_gap_lower_bound_mm':lower,'profile_chord_error_bound_mm':chord_error}
