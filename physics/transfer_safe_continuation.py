"""Conservative centerline interpolation bounds for moving solids."""
import numpy as np

def transition_bounds(old,new,old_state,new_state,old_gap,new_gap,old_self,new_self,radius):
 displacement=float(np.max(np.linalg.norm(new-old,axis=1)))
 du,dg,dh=np.array(new_state)-old_state
 rigid=max(abs(du),abs(du-dg),abs(dh))
 return {'max_node_motion_mm':displacement,'max_rigid_motion_mm':float(rigid),
  'solid_centerline_bound_mm':float(min(old_gap,new_gap)+radius-.5*(displacement+rigid)),
  'nonlocal_centerline_bound_mm':float(min(old_self,new_self)+2*radius-displacement)}
