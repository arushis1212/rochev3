"""Coupled rod, cloth clamp and gravity feeder energy in millimetres and newtons."""
import numpy as np
from physics.connected_yarn import connected_objective
from physics.loop_holding import bar_direction,contact_counts
from physics.feeder_domain import feeder_potential
from physics.roche_contact3d import contact_energy3d,self_contact,self_pairs
from physics.bordered_newton import bordered_hessian
from physics.banded_newton import banded_hessian

class FeedEquilibrium:
 def __init__(self,q,rest,split,center,angles,z,cfg,obstacle,feeder,mode):
  self.q=np.asarray(q);self.rest=np.asarray(rest);self.split=split;self.cfg=cfg;self.obstacle=obstacle;self.feeder=feeder;self.mode=mode;self.nip=self.q[-1].copy()
  self.free=np.array([i for i in range(len(q))if i not in [0,split,len(q)-1]]);self.interior=3*len(self.free);self.counts=contact_counts(self.rest,cfg);self.pairs=self_pairs(self.rest,cfg['yarn_radius_mm']);self.x0=self.pack(q,center,angles,z)
 def pack(self,q,center,angles,z):return np.r_[np.asarray(q)[self.free].ravel(),center,angles,z]
 def unpack(self,x):
  m=self.interior;q=self.q.copy();q[self.free]=x[:m].reshape(-1,3);c=x[m:m+3];a=x[m+3:m+5];z=x[-1]
  q[[0,self.split]]=c+np.asarray(self.cfg['active_attachment_offsets_x_mm'])[:,None]*bar_direction(a)[0];q[-1]=self.nip
  return q,c,a,z
 def energy(self,x):
  q,c,a,z=self.unpack(x);self.obstacle.moving.center[2]=z;V,dV,_=feeder_potential(z,self.feeder,self.mode)
  E,g,cg,ag,self.last_info=connected_objective(q,self.rest,self.split,c,a,self.nip,self.cfg,self.obstacle)
  _,mg=contact_energy3d(q,self.rest,self.cfg['yarn_radius_mm'],self.cfg['penalty_N_per_mm2'],self.obstacle.moving,self.counts)
  return E+V,np.r_[g[self.free].ravel(),cg,ag,dV-mg[:,2].sum()]
 def safe_energy(self,x):
  try:return self.energy(x)
  except ValueError:return float('inf'),np.zeros_like(x)
 def local_safe(self,x):return self_contact(self.unpack(x)[0],self.rest,self.cfg['yarn_radius_mm'],self.cfg['penalty_N_per_mm2'],self.pairs)[2]>4e-6
 def hessian(self,x,step=1e-8):
  n=len(x);H=np.zeros((n,n));m=self.interior
  if self.local_safe(x):
   A,B,C=bordered_hessian(self.energy,x,m,step=step);H[:m,m:]=B;H[m:,:m]=B.T;H[m:,m:]=C
  else:A=banded_hessian(self.energy,x,n-1,step);m=n
  for k in range(A.shape[0]):
   j=np.arange(m-k);H[j+k,j]=A[k,:m-k];H[j,j+k]=A[k,:m-k]
  return H
 def checkpoint(self,x,state):
  q,c,a,z=self.unpack(x)
  return {'q':q.tolist(),'rest':self.rest.tolist(),'split':self.split,'center':c.tolist(),'angles':a.tolist(),'feeder_z':float(z),'state':list(state),'accepted_motion':False,'scope':'Numerical whole-material endpoint; admission requires force, contact, capture and trajectory checks'}
