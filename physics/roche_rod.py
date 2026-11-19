"""Quasistatic planar extensible rod with bending and finite-radius contact.
Units: mm,N,N*mm. Isotropic bend, no twist/friction/self-contact in this local test.
"""
import numpy as np
from physics.banded_newton import minimize_banded

def energy_gradient(q,rest,EA,B):
    e=np.diff(q,axis=0);length=np.linalg.norm(e,axis=1)
    if np.min(length)<1e-10:raise ValueError('Collapsed rod edge')
    t=e/length[:,None];stretch=length-rest
    energy=float(np.sum(EA*stretch**2/(2*rest)))
    edge_grad=(EA*stretch/rest)[:,None]*t
    g=np.zeros_like(q);g[:-1]-=edge_grad;g[1:]+=edge_grad
    dot=np.einsum('ij,ij->i',t[:-1],t[1:]);dual=(rest[:-1]+rest[1:])/2
    if np.min(1+dot)<1e-8:raise ValueError('Folded rod singularity')
    # |curvature binormal|^2=4(1-cos theta)/(1+cos theta).
    energy+=float(np.sum(2*B/dual*(1-dot)/(1+dot)))
    dEdc=-4*B/(dual*(1+dot)**2)
    da=dEdc[:,None]*(t[1:]-dot[:,None]*t[:-1])/length[:-1,None]
    db=dEdc[:,None]*(t[:-1]-dot[:,None]*t[1:])/length[1:,None]
    g[:-2]-=da;g[1:-1]+=da-db;g[2:]+=db
    return energy,g

def box_distance(p,half_width,bottom,top):
    center=np.array([0.,(bottom+top)/2]);half=np.array([half_width,(top-bottom)/2])
    delta=p-center;excess=np.abs(delta)-half;outer=np.maximum(excess,0.)
    n=np.linalg.norm(outer,axis=1);distance=n+np.minimum(np.max(excess,axis=1),0.)
    grad=np.zeros_like(p);outside=n>1e-14
    grad[outside]=outer[outside]/n[outside,None]*np.sign(delta[outside])
    inside=~outside;idx=np.argmax(excess[inside],axis=1)
    sub=grad[inside];v=delta[inside];sub[np.arange(len(idx)),idx]=np.where(v[np.arange(len(idx)),idx]>=0,1.,-1.);grad[inside]=sub
    return distance,grad

def contact_energy(q,radius,k,box,samples=4,rest=None):
    # Interior samples are integration points; independent dense capsule-distance
    # check below bounds any between-sample missed penetration by Lipschitzness.
    ts=(np.arange(samples)+.5)/samples
    points=(1-ts)[None,:,None]*q[:-1,None,:]+ts[None,:,None]*q[1:,None,:]
    d,n=box_distance(points.reshape(-1,2),**box);depth=np.maximum(radius-d,0.)
    weights=np.repeat(np.ones(len(q)-1) if rest is None else rest,samples)
    energy=.5*k*np.dot(weights*depth,depth)/samples
    gp=(-k*(weights*depth)[:,None]*n/samples).reshape(len(q)-1,samples,2)
    grad=np.zeros_like(q);grad[:-1]+=np.sum((1-ts)[None,:,None]*gp,axis=1);grad[1:]+=np.sum(ts[None,:,None]*gp,axis=1)
    return float(energy),grad

def solve(q,rest,EA,B,radius,box,k=100.,samples=4,maxiter=1000):
    endpoints=q[[0,-1]].copy();start=q[1:-1].ravel()
    def evaluate(x):
        p=np.vstack([endpoints[0],x.reshape(-1,2),endpoints[1]])
        a,g=energy_gradient(p,rest,EA,B);b,h=contact_energy(p,radius,k,box,samples,rest)
        return a+b,(g+h)[1:-1].ravel()
    x,diagnostic=minimize_banded(evaluate,start,bandwidth=5,maxiter=min(maxiter,300))
    p=np.vstack([endpoints[0],x.reshape(-1,2),endpoints[1]])
    return p,diagnostic


def clearance_bound(q,radius,box,spacing=.005):
    # Signed distance to a closed solid is1-Lipschitz. For each segment all its
    # points are within half the sample spacing of a checked point.
    minimum=float('inf');bound=float('inf')
    for a,b in zip(q[:-1],q[1:]):
        length=float(np.linalg.norm(b-a));n=max(1,int(np.ceil(length/spacing)));pts=a+(b-a)*np.linspace(0,1,n+1)[:,None]
        d,_=box_distance(pts,**box);m=float(np.min(d))-radius;minimum=min(minimum,m);bound=min(bound,m-length/(2*n))
    return {'sampled_centerline_surface_gap_mm':minimum,'continuous_polyline_gap_lower_bound_mm':bound,'sampling_spacing_max_mm':spacing}


def transition_clearance_bound(a,b,radius,box,max_motion_spacing=.01):
    motion=float(np.max(np.linalg.norm(b-a,axis=1)))
    steps=max(1,int(np.ceil(motion/max_motion_spacing)))
    lower=min(clearance_bound((1-t)*a+t*b,radius,box)['continuous_polyline_gap_lower_bound_mm'] for t in np.linspace(0,1,steps+1))
    return lower-motion/(2*steps)
