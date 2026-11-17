"""Conservative centerline bounds and local transfer scheduling utilities."""
import numpy as np

def transition_bounds(old,new,old_state,new_state,old_gap,new_gap,old_self,new_self,radius):
 displacement=float(np.max(np.linalg.norm(new-old,axis=1)))
 du,dg,dh=np.array(new_state)-old_state
 rigid=max(abs(du),abs(du-dg),abs(dh))
 return {'max_node_motion_mm':displacement,'max_rigid_motion_mm':float(rigid),
  'solid_centerline_bound_mm':float(min(old_gap,new_gap)+radius-.5*(displacement+rigid)),
  'nonlocal_centerline_bound_mm':float(min(old_self,new_self)+2*radius-displacement)}

def transfer_schedule(candidate,safe):
 adv=candidate['advance_mm'];gate=candidate['gate_open_mm'];high=candidate['lift_high_v_mm']-candidate['lift_park_v_mm']
 def ramp(a,b,step):
  if step<=0:raise ValueError('Positive motion increment required')
  return np.linspace(a,b,max(1,int(np.ceil(abs(b-a)/step)))+1)[1:]
 full=safe.get('include_initial_advance',False)
 schedule=[('advance',[float(u),gate,0.]) for u in ramp(0,adv,safe['advance_increment_mm'])] if full else []
 schedule += [('lift',[adv,gate,float(h)]) for h in ramp(0 if full else 4.,high,safe['lift_increment_mm'])]
 schedule += [('close',[adv,float(g),high]) for g in ramp(gate,0,safe['gate_increment_mm'])]
 schedule += [('castoff',[float(u),0.,high]) for u in ramp(adv,-8.5,safe['castoff_increment_mm'])]
 return schedule
