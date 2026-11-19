"""T3 holding load path with finite physical guides and free hanging clamp."""
from pathlib import Path
import sys,json,os,time,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from spec.effective import load_fixture
import numpy as np
from functools import lru_cache
from physics.auxiliary_contact import AuxiliaryContact
from physics.compiled_profile import prepare_profile

@lru_cache(maxsize=1)
def auxiliary_envelopes():
 return json.loads((Path(__file__).resolve().parents[1]/'cad/transfer/generated/auxiliary_envelopes.json').read_text())

from physics.transfer_contact import TransferContact,transfer_metrics
from physics.loop_holding import head_frame,solve_holding
from physics.roche_contact3d import extrusion_distance,extrusion_contact_distance,gap_bound

class WorldTransfer:
 def __init__(self,profiles,baseprofiles,tip,advance,gate,lift,reset=0.):
  profiles={k:prepare_profile(v)for k,v in profiles.items()};baseprofiles={k:prepare_profile(v)for k,v in baseprofiles.items()}
  self.origin,self.frame=head_frame(tip);self.local=TransferContact(profiles,advance,gate,lift_mm=lift,reset_mm=reset);self.baseprofiles=baseprofiles;self.auxiliary=AuxiliaryContact(auxiliary_envelopes(),lift,advance,gate,reset)
 def components(self,p):
  parts=[(d,g@self.frame.T) for d,g in self.local.components((p-self.origin)@self.frame)]
  parts += [(d,g@self.frame.T) for d,g in self.auxiliary.components((p-self.origin)@self.frame)]
  parts.append(extrusion_distance(p,self.baseprofiles['B06_knockover']))
  return parts
 def edge_contact_terms(self,q,rest,counts,radius):
  from physics.edge_contact import world_edge_terms
  return world_edge_terms(self,q,rest,counts,radius)
 def sparse_components(self,p,radius):
  from physics.sparse_contact import world_terms
  return world_terms(self,p,radius)
 def contact_components(self,p,radius):
  parts=[(d,g@self.frame.T) for d,g in self.local.contact_components((p-self.origin)@self.frame,radius)]
  parts += [(d,g@self.frame.T) for d,g in self.auxiliary.contact_components((p-self.origin)@self.frame,radius)]
  parts.append(extrusion_contact_distance(p,self.baseprofiles['B06_knockover'],radius))
  return parts
 def distance(self,p):
  parts=self.components(p);d,g=parts[0]
  for x,n in parts[1:]:
   use=x<d;d[use]=x[use];g[use]=n[use]
  return d,g

def initial_route(cfg):
 center=np.array(cfg['clamp_initial_center_xyz_mm']);ends=center+np.array(cfg['active_attachment_offsets_x_mm'])[:,None]*[1.,0.,0.];origin,M=head_frame(cfg['head_tip_xyz_mm']);w=cfg['initial_route_w_mm'];v=cfg['initial_route_knee_v_mm'];knee=[origin+M@np.array([0.,v,z]) for z in [-w,w]];top=[origin+M@np.array([0.,0.,z]) for z in [-w,w]]
 left=np.vstack([np.linspace(ends[0],knee[0],cfg['outer_leg_segments']+1),np.linspace(knee[0],top[0],cfg['inner_leg_segments']+1)[1:]])
 bridge=np.linspace(top[0],top[1],cfg['bridge_segments']+1)[1:]
 right=np.vstack([np.linspace(top[1],knee[1],cfg['inner_leg_segments']+1)[1:],np.linspace(knee[1],ends[1],cfg['outer_leg_segments']+1)[1:]])
 q=np.vstack([left,bridge,right]);return q,np.linalg.norm(np.diff(q,axis=0),axis=1),center,np.zeros(2)
