"""Exact native-solid swept checks for hardware outside analytical contact shapes.

At a fixed tool/guide pose, feeder carrier parts translate in Z. The weight cup
follows the monotone cord equation. Rigid cloth-clamp parts are represented by
native-verified rotating box unions. Every other installed part is queried here.
The native edge distance is 1-Lipschitz in both geometric operands; segment speed
is bounded by the faster endpoint. No tessellation or point-only collision test.
"""
import numpy as np
from physics.feed_native import hardware
from cad.transfer import installation as install
from physics.feeder_domain import feeder_potential

EXACT_CONTACT_NAMES={
 'TOOL_H01_hook_body','TOOL_H02_gate','TRANSFER_R01_front_stripper','TRANSFER_R02_rear_stripper','TRANSFER_R03_lift_pin_0','TRANSFER_R03_lift_pin_1',
 'B01_bed','B02_cover','B06_knockover','D03_return_pin','GUIDE_TOOL_G01_guide_tube','GUIDE_TOOL_G03_outer_tube','GUIDE_TOOL_G06_exit_insert','GUIDE_TOOL_G07_exit_reducer','P11_fairlead','P15_pad_lower','P15_pad_upper',
 *[f'P05_{name}_{half}'for name in ['left','right','moving']for half in [0,1]],
 *[f'{name}_{side}'for name in ['D01_jaw','D02_pad']for side in ['A','B']],
 *[f'{name}_{i}'for name in ['HW_M3x16_cloth','HW_M3nut_cloth','D04_stop_spacer']for i in range(4)]}

def carrier_part(name):
 return name=='P04_carrier' or name.endswith('_moving') or '_pulley_moving_'in name or name.startswith('P05_moving_')

def aabb_lower(q,lo,hi):
 elo=np.minimum(q[:-1],q[1:]);ehi=np.maximum(q[:-1],q[1:]);return np.linalg.norm(np.maximum(np.maximum(lo-ehi,elo-hi),0),axis=1)

class NativeRemainderGuard:
 def __init__(self,model,state,guide,allowance=.01,max_depth=7):
  self.model=model;self.state=list(state);self.guide=list(guide);self.allowance=allowance;self.max_depth=max_depth;self.z0=float(model.x0[-1]);self.cz0=feeder_potential(self.z0,model.feeder,model.mode)[2];q,c,a,z=model.unpack(model.x0);ps,tp=hardware();scene=install.installed(ps,tp,*state[:3],self.guide,reset=state[3],carrier_z=z,feed_mode=model.mode.lower(),clamp_pose=(c,a));self.parts=[];self.represented=[]
  missing=EXACT_CONTACT_NAMES-set(scene)
  if missing:raise ValueError('Native contact coverage name missing: '+str(sorted(missing)))
  for name,shape in scene.items():
   if name in EXACT_CONTACT_NAMES:self.represented.append(name);continue
   b=shape.BoundingBox();kind='carrier'if carrier_part(name)else'counter'if name=='P18_weight_cup'else'fixed';self.parts.append((name,shape,np.array([b.xmin,b.ymin,b.zmin]),np.array([b.xmax,b.ymax,b.zmax]),kind))
  self.inventory={'native_solids':len(scene),'analytical_contact_solids':sorted(self.represented),'native_remainder_solids':[p[0]for p in self.parts],'scope':'Fixed head/guide/support pose; every native solid either in the analytical contact set or the exact swept remainder. Analytical set requires its CAD equivalence/enclosure evidence.'};self.last=None
 def __call__(self,a,b,deadline_check=lambda:None):
  m=self.model;delta=np.asarray(b)-a;n=m.interior;speed=np.zeros(len(m.q));speed[m.free]=np.linalg.norm(delta[:n].reshape(-1,3),axis=1);speed[getattr(m,'fixed_indices',[0,m.split])]=m.step_speed_bounds(delta)[0];edge_speed=np.maximum(speed[:-1],speed[1:]);radius=m.cfg['yarn_radius_mm'];leaves=[(0.,1.,0)];queries=0;intervals=0;minimum=float('inf');worst=None
  while leaves:
   deadline_check();lo,hi,depth=leaves.pop();t=(lo+hi)/2;half=(hi-lo)/2;q=m.unpack(a+t*delta)[0];zl=float(a[-1]+lo*delta[-1]);zh=float(a[-1]+hi*delta[-1]);zm=(zl+zh)/2;czl=feeder_potential(zl,m.feeder,m.mode)[2];czh=feeder_potential(zh,m.feeder,m.mode)[2];czm=feeder_potential(zm,m.feeder,m.mode)[2];interval_min=float('inf');actual_min=float('inf');interval_worst=None;lines={};intervals+=1
   for name,shape,low,high,kind in self.parts:
    shift=zm-self.z0 if kind=='carrier'else czm-self.cz0 if kind=='counter'else 0.;rigid=max(abs(zl-zm),abs(zh-zm))if kind=='carrier'else max(abs(czl-czm),abs(czh-czm))if kind=='counter'else 0.;offset=np.array([0.,0.,shift]);lower=aabb_lower(q,low+offset,high+offset);motion=edge_speed*half+rigid;bounds=lower-radius-motion
    ids=np.flatnonzero(bounds < -self.allowance)
    for j in ids:
     deadline_check();key=(int(j),shift)
     if key not in lines:lines[key]=install.base.cq.Edge.makeLine(install.base.cq.Vector(*(q[j]-offset)),install.base.cq.Vector(*(q[j+1]-offset)))
     distance=float(lines[key].distance(shape));queries+=1;actual=distance-radius;bound=actual-motion[j];bounds[j]=bound
     if actual<actual_min:actual_min=actual
    j=int(np.argmin(bounds));value=float(bounds[j])
    if value<interval_min:interval_min=value;interval_worst=[name,j]
   if interval_min>=-self.allowance:
    if interval_min<minimum:minimum=interval_min;worst=interval_worst
    continue
   if actual_min< -self.allowance or depth>=self.max_depth:
    self.last={'certified':False,'reason':'native_contact_or_unresolved_interval','fraction':t,'depth':depth,'minimum_bound_mm':interval_min,'worst':interval_worst,'queries':queries,'intervals':intervals};return False
   leaves.extend([(lo,t,depth+1),(t,hi,depth+1)])
  self.last={'certified':True,'minimum_bound_mm':minimum,'worst':worst,'queries':queries,'intervals':intervals,'allowance_mm':self.allowance,'remainder_solids':len(self.parts)};return True
