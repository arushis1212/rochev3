"""Independent native-solid clearance for upstream material and current assembly."""
from functools import lru_cache
import numpy as np
from cad.transfer import installation as install
from cad.transfer.build import parts

@lru_cache(maxsize=1)
def hardware():return install.base.parts(),parts()

def upstream_clearance(q,state,guide,z=160,mode='LOW',radius=.3,clamp_pose=None,
                       fixed_section=None,edge_offset=0,nip_section=None,current_machine_state=None):
 """Native checks with bounded own-pad reductions only for registered grips.

 edge_offset explicitly maps a sliced q back to full material edge identities.
 Every other solid and every unregistered edge uses the original native shape.
 """
 q=np.asarray(q,dtype=float)
 if q.ndim!=2 or q.shape[1]!=3 or len(q)<2 or not np.isfinite(q).all():
  raise ValueError('Native clearance requires a finite material polyline with at least two nodes')
 if not np.isfinite(radius) or radius<=0:raise ValueError('Native yarn radius must be positive and finite')
 if len(state)!=4 or not np.isfinite(state).all() or len(guide)!=3 or not np.isfinite(guide).all() or not np.isfinite(z):
  raise ValueError('Native hardware pose must be finite and fully specified')
 if mode.upper() not in ('LOW','HIGH'):raise ValueError('Unknown physical feeder mode')
 if type(edge_offset)is not int or edge_offset<0:raise ValueError('Invalid material edge offset')
 ps,tp=hardware();a,g,h,r=state
 if current_machine_state is None:
  scene=install.installed(ps,tp,a,g,h,list(guide),reset=r,carrier_z=z,feed_mode=mode.lower(),clamp_pose=clamp_pose)
  nip_names=('P15_pad_lower','P15_pad_upper')
 else:
  from cad.machine import assembly as machine
  if nip_section and current_machine_state.get('inlet_nip','CLOSED')!='CLOSED':
   raise ValueError('Registered inlet material cannot be fixed while its actual nip is open')
  scene=machine.installed(ps,tp,advance=a,gate=g,lift=h,reset=r,guide=list(guide),carrier_z=z,
                          feed_mode=mode.lower(),clamp_pose=clamp_pose,**current_machine_state)
  nip_names=('NIP_NS06_lower_pad_IN','NIP_NS07_upper_pad_IN')
 contacts=[];minimum=float('inf');worst=None;exact=0
 clamp=None;cutters={};reduced={};applied=[];nip_grip=None;nip_cutters={}
 if nip_section:
  from physics.nip_grip import NipGrip
  nip_grip=NipGrip(install.base.S['feeder'],nip_section,len(q)+edge_offset)
  local_ids=nip_grip.indices-edge_offset;visible=local_ids>=0
  if not np.allclose(np.asarray(q)[local_ids[visible]],nip_grip.xyz[visible],atol=1e-10,rtol=0):
   raise ValueError('Native query differs from prescribed nip material coordinates')
  for edge in nip_grip.edge_ids:
   lo,hi=nip_grip.cut_for_edge(edge);nip_cutters[edge]=install.base.box(lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]).val()
 if fixed_section and fixed_section.get('gripped_edges'):
  if clamp_pose is None:raise ValueError('Registered native grip checks require clamp pose')
  from physics.fixture_contact import ClampContact
  clamp=ClampContact(install.base.S['cloth_clamp'],*clamp_pose,fixed_section=fixed_section)
  yaw,pitch,roll=clamp.angles*180/np.pi/clamp.spec['angular_scale_mm']
  for edge,(lo,hi)in clamp.grip_regions.items():
   cutter=install.base.box(lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]).val()
   cutters[edge]=cutter.rotate((0,0,0),(1,0,0),float(roll)).rotate((0,0,0),(0,1,0),float(-pitch)).rotate((0,0,0),(0,0,1),float(yaw)).translate(tuple(clamp.center))
 shapes=[]
 for name,shape in scene.items():
  b=shape.BoundingBox();shapes.append((name,shape,np.array([b.xmin,b.ymin,b.zmin]),np.array([b.xmax,b.ymax,b.zmax])))
 for edge,(x,y)in enumerate(zip(q[:-1],q[1:])):
  material_edge=edge+edge_offset
  elo=np.minimum(x,y);ehi=np.maximum(x,y);line=None
  for name,shape,lo,hi in shapes:
   lower=float(np.linalg.norm(np.maximum(np.maximum(lo-ehi,elo-hi),0)))
   if lower>radius+.01:gap=lower-radius
   else:
    if line is None:line=install.base.cq.Edge.makeLine(install.base.cq.Vector(*x),install.base.cq.Vector(*y))
    target=shape
    if name in ('D02_pad_A','D02_pad_B') and material_edge in cutters:
     key=(name,material_edge)
     if key not in reduced:
      reduced[key]=shape.cut(cutters[material_edge]);applied.append({'part':name,'material_edge':material_edge})
     target=reduced[key]
    if name in nip_names and nip_grip and material_edge in nip_grip.edge_ids:
     key=(name,material_edge)
     if key not in reduced:
      reduced[key]=shape.cut(nip_cutters[material_edge]);applied.append({'part':name,'material_edge':material_edge})
     target=reduced[key]
    gap=float(line.distance(target))-radius;exact+=1
   if gap<minimum:minimum=gap;worst=[name,edge]
   if gap<-.01:contacts.append({'part':name,'edge':edge,'gap_mm':gap})
 return {'assembly_solids':len(scene),'minimum_gap_lower_bound_mm':minimum,'worst_part_edge':worst,'violations':contacts,'exact_queries':exact,
         'grip_exclusions':None if clamp is None else {**clamp.grip_exclusion_metadata(),'applied_native_reductions':applied,'material_edge_offset':edge_offset},
         'nip_grip_exclusions':None if nip_grip is None else {**nip_grip.metadata(),
            'applied_native_reductions':[x for x in applied if x['part'] in nip_names],
            'material_edge_offset':edge_offset},
         'assembly_configuration':'D26 composed indexed/service machine' if current_machine_state is not None else 'single-station diagnostic fixture',
         'scope':'Material edges against full native scene at specified feeder height and mode; explicitly listed own-pad grip reductions are conditional boundary assumptions, not retention evidence. No swept-path certificate.'}
