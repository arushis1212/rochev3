"""Euclidean signed distance to a finite pin minus an upward capsule channel.

The pin axis is body Y, the channel axis body Z. This is a geometric distance,
not max/min composition of primitive signed fields. Every point sees the same
solid; there is no material-index mask. See docs/BORED_PIN_DISTANCE.md.
"""
from __future__ import annotations
import numpy as np


class BoredPinCapsuleDistance:
    def __init__(self, center, radius, half_length, channel_radius, channel_lower_center_z):
        c=np.asarray(center,float)
        values=np.asarray([radius,half_length,channel_radius,channel_lower_center_z],float)
        if c.shape!=(3,) or not np.isfinite(c).all() or not np.isfinite(values).all():
            raise ValueError('Finite pin geometry required')
        R,L,r,z=map(float,values)
        # These inequalities keep the lower hemisphere strictly inside the pin
        # and its end faces uncut; other geometries require another feature set.
        if not (0<r<z and z+r<R and r<L):
            raise ValueError('Channel hemisphere must lie strictly inside finite pin')
        self.center=c.copy();self.R=R;self.L=L;self.r=r;self.z=z

    def _rim_points(self,p):
        """Global nearest point on the actual upper cylinder intersection."""
        R,r=self.R,self.r;a,b=np.abs(p[:,0]),np.abs(p[:,1]);c=p[:,2]
        lo=np.zeros(len(p));hi=np.full(len(p),np.pi/2)
        # With b=0 the endpoint derivative has a removable zero. Its one-sided
        # t derivative decides whether the minimum is at x=r, y=0.
        endpoint=(b==0)&(-r-a+c*r/np.sqrt((R-r)*(R+r))<=0)
        for _ in range(56):
            theta=(lo+hi)/2;t=r*np.sin(theta);y=r*np.cos(theta)
            z=np.sqrt((R-t)*(R+t))
            derivative=(-t-a)*y+b*t+c*t*y/z
            negative=derivative<=0
            lo=np.where(negative,theta,lo);hi=np.where(negative,hi,theta)
        theta=np.where(endpoint,np.pi/2,(lo+hi)/2)
        x=r*np.sin(theta);y=r*np.cos(theta)
        x=np.where(endpoint,r,x);y=np.where(endpoint,0.,y)
        return np.column_stack((np.where(p[:,0]<0,-x,x),np.where(p[:,1]<0,-y,y),np.sqrt((R-x)*(R+x))))

    def distance(self,points):
        p=np.asarray(points,float)
        if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():
            raise ValueError('Finite N by 3 point array required')
        p=p-self.center;N=len(p)
        if not np.isfinite(p).all():raise ValueError('Relative pin coordinates overflow')
        if N==0:return np.empty(0),np.empty((0,3))
        R,L,r,zc=self.R,self.L,self.r,self.z
        rho=np.hypot(p[:,0],p[:,2]);radial=np.hypot(p[:,0],p[:,1])
        # Side of the original finite pin, retaining only uncut points.
        side=np.column_stack((np.divide(R*p[:,0],rho,out=np.full(N,R),where=rho>0),np.clip(p[:,1],-L,L),np.divide(R*p[:,2],rho,out=np.zeros(N),where=rho>0)))
        channel_delta=side-np.column_stack((np.zeros(N),np.zeros(N),np.maximum(side[:,2],zc)))
        side_valid=np.linalg.norm(channel_delta,axis=1)>=r
        side_normal=np.column_stack((side[:,0]/R,np.zeros(N),side[:,2]/R))
        # Complete end disks are not intersected by this channel.
        end_radial=np.minimum(1.,np.divide(R,rho,out=np.ones(N),where=rho>0))
        lower=np.column_stack((p[:,0]*end_radial,np.full(N,-L),p[:,2]*end_radial))
        upper=lower.copy();upper[:,1]=L
        # Radial projection to the channel wall. It is valid only between its
        # equator and the actual upper intersection; no fictitious extension.
        cx=np.divide(r*p[:,0],radial,out=np.zeros(N),where=radial>0)
        cy=np.divide(r*p[:,1],radial,out=np.full(N,r),where=radial>0)
        cap_z=np.sqrt((R-cx)*(R+cx))
        wall=np.column_stack((cx,cy,np.clip(p[:,2],zc,cap_z)))
        wall_untrimmed=(p[:,2]>=zc)&(p[:,2]<=cap_z)
        wall_normal=np.column_stack((-cx/r,-cy/r,np.zeros(N)))
        # Lower hemisphere; its equator joins the wall smoothly.
        sphere_delta=p-[0.,0.,zc];length=np.linalg.norm(sphere_delta,axis=1)
        sphere=np.divide(r*sphere_delta,length[:,None],out=np.tile([0.,0.,-r],(N,1)),where=length[:,None]>0)+[0.,0.,zc]
        use_equator=p[:,2]>zc
        sphere[use_equator]=np.column_stack((cx,cy,np.full(N,zc)))[use_equator]
        sphere_normal=-(sphere-[0.,0.,zc])/r
        candidates=[side,lower,upper,wall,sphere]
        normals=[side_normal,np.tile([0.,-1.,0.],(N,1)),np.tile([0.,1.,0.],(N,1)),wall_normal,sphere_normal]
        ds=np.array([np.linalg.norm(p-q,axis=1) for q in candidates]);ds[0,~side_valid]=np.inf
        # The rim is a subset of both untrimmed side and wall surfaces. If
        # either global projection is valid, it cannot be farther than the rim.
        need_rim=~(side_valid|wall_untrimmed)
        rim=wall.copy()
        if np.any(need_rim):rim[need_rim]=self._rim_points(p[need_rim])
        rim_distance=np.linalg.norm(p-rim,axis=1);rim_distance[~need_rim]=np.inf
        ds=np.vstack((ds,rim_distance));candidates.append(rim)
        rim_normal=np.column_stack((rim[:,0]/R,np.zeros(N),rim[:,2]/R));normals.append(rim_normal)
        winner=np.argmin(ds,axis=0);idx=np.arange(N);closest=np.array(candidates)[winner,idx];distance=ds[winner,idx]
        if not np.isfinite(distance).all():raise ValueError('Pin distance is not numerically finite')
        fallback=np.array(normals)[winner,idx]
        channel_vec=p-np.column_stack((np.zeros(N),np.zeros(N),np.maximum(p[:,2],zc)))
        inside=(rho<R)&(np.abs(p[:,1])<L)&(np.linalg.norm(channel_vec,axis=1)>r)
        sign=np.where(inside,-1.,1.)
        normal=np.divide(p-closest,distance[:,None],out=fallback.copy(),where=distance[:,None]>1e-14)
        normal*=sign[:,None]
        # A zero-distance point uses the authored outward boundary normal.
        zero=distance<=1e-14;normal[zero]=fallback[zero]
        return sign*distance,normal
