"""World-coordinate contacts for the mechanically guided transfer station."""
from pathlib import Path
import json
import numpy as np
from functools import lru_cache
from physics.auxiliary_contact import AuxiliaryContact
from physics.compiled_profile import prepare_profile
from physics.transfer_contact import TransferContact
from physics.loop_holding import head_frame
from physics.roche_contact3d import extrusion_distance,extrusion_contact_distance

@lru_cache(maxsize=1)
def auxiliary_envelopes():
 return json.loads((Path(__file__).resolve().parents[1]/'cad/transfer/generated/auxiliary_envelopes.json').read_text())

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
