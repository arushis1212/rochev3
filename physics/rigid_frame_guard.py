"""Separate world-solid and body-relative clamp distance certificates.
Rigid common motion cancels exactly in the clamp frame. No gap is relaxed.
"""
import numpy as np
from physics.rigid_clamp import rotation
from physics.collision_aware_steps import certify_configuration_path
class RigidFrameFeedGuard:
 def __init__(self,model,allowance=.01,max_depth=7,spacing=.004):
  self.model=model;self.allowance=allowance;self.max_depth=max_depth;self.spacing=spacing;self.last=None;self.accepted=0;self.rejected=0
 def __call__(self,a,b):
  m=self.model;delta=np.asarray(b)-a;n=m.interior;qa,ca,aa,za=m.unpack(a);qb,cb,ab,zb=m.unpack(b);speed=np.zeros(len(qa));speed[m.free]=np.linalg.norm(delta[:n].reshape(-1,3),axis=1);speed[m.fixed_indices]=m.step_speed_bounds(delta)[0];parts=m.obstacle.fixed
  try:
   m.obstacle.fixed=[p for p in parts if p is not m.clamp]
   def world(t):m.set_obstacle_pose(a+t*delta);return m.obstacle
   common=dict(rest=m.rest,radius=m.cfg['yarn_radius_mm'],allowance=self.allowance,max_depth=self.max_depth,spacing=self.spacing)
   first=certify_configuration_path(lambda t:m.unpack(a+t*delta)[0],world,speed,abs(zb-za),pairs=m.pairs,**common)
   if not first['certified']:self.last=first;self.rejected+=1;return False
   # Free nodes and COM interpolate linearly. Their relative norm is bounded
   # by the larger endpoint norm; rotating into the body adds |r|*sum|dangle|.
   relative=np.linalg.norm((qb-qa)-(cb-ca),axis=1)+np.maximum(np.linalg.norm(qa-ca,axis=1),np.linalg.norm(qb-cb,axis=1))*sum(abs(ab-aa))/m.angle_scale;relative[m.fixed_indices]=0.
   def body(t):
    q,c,angles,z=m.unpack(a+t*delta);R,_=rotation(angles,m.angle_scale);return(q-c)@R
   m.clamp.set_pose(np.zeros(3),np.zeros(3))
   second=certify_configuration_path(body,lambda t:m.clamp,relative,0.,pairs=(np.array([],dtype=int),np.array([],dtype=int)),**common)
   self.last={'certified':bool(second['certified']),'world':first,'clamp_body_frame':second,'scope':'World solids/self contact plus exact body-relative clamp contact; same numerical allowance.'}
   if second['certified']:self.accepted+=1
   else:self.rejected+=1
   return second['certified']
  finally:m.obstacle.fixed=parts;m.set_obstacle_pose(a)
