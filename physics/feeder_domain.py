"""Material-conserving upstream yarn and translating gravity feeder (ideal frictionless)."""
import numpy as np
from physics.guide_contact import annular_cylinder
from physics.edge_contact import edge_samples
from physics.roche_contact3d import contact_energy3d
from physics.r5_feed_geometry import counter_center
from physics.auxiliary_contact import box_distance3d

class Pulley:
 def __init__(self,x,z):self.center=np.array([x,406.,z]);self.axis=np.array([0.,1.,0.])
 def components(self,p):return [annular_cylinder(p,self.axis,self.center,lo,hi,inner,outer) for lo,hi,inner,outer in [(-1.5,1.5,5.1,8.),(-3,-1.5,4.3,10.),(1.5,3,4.3,10.)]]
 def distance(self,p):
  components=self.components(p);d,g=components[0]
  for x,n in components[1:]:
   mask=x<d;d[mask]=x[mask];g[mask]=n[mask]
  return d,g
 def edge_contact_terms(self,q,rest,counts,radius):
  lo=self.center+[-10,-3,-10];hi=self.center+[10,3,10];e,t,w,p=edge_samples(q,rest,counts,lo,hi,radius)
  if len(e):
   d,g=self.distance(p);yield e,t,w,d,g

class Fairlead:
 def distance(self,p):return annular_cylinder(p,np.array([1.,0,0]),np.array([102.,406,238]),-5,5,1.5,3)
 def edge_contact_terms(self,q,rest,counts,radius):
  e,t,w,p=edge_samples(q,rest,counts,[97,403,235],[107,409,241],radius)
  if len(e):
   d,g=self.distance(p);yield e,t,w,d,g

class NipPads:
 boxes=[([10,401,238],[22,411,238.5]),([10,401,239.1],[22,411,239.6])]
 def __init__(self,feeder=None):
  self.grip=None
  if feeder:
   gap=feeder['nip_closed_gap_mm'];self.boxes=[([10,401,238],[22,411,238.5]),([10,401,238.5+gap],[22,411,239.+gap])]
 def set_grip(self,grip):self.grip=grip;self.reduced={e:grip.reduce(self.boxes,e)for e in grip.edge_ids}
 def distance_for_edges(self,p,edge_ids):
  d,g=self.distance(p)
  if self.grip:
   for edge,reduced in self.reduced.items():
    use=np.asarray(edge_ids)==edge;x,n=reduced.distance(p[use]);d[use]=x;g[use]=n
  return d,g
 def distance(self,p):
  d,g=box_distance3d(p,*self.boxes[0]);x,n=box_distance3d(p,*self.boxes[1]);mask=x<d;d[mask]=x[mask];g[mask]=n[mask];return d,g
 def edge_contact_terms(self,q,rest,counts,radius):
  for lo,hi in self.boxes:
   e,t,w,p=edge_samples(q,rest,counts,lo,hi,radius)
   if len(e):
    d,g=box_distance3d(p,lo,hi)
    if getattr(self,'grip',None):
     from physics.fixture_contact import BoxUnion,subtract_box
     for edge in self.grip.edge_ids:
      reduced=BoxUnion(subtract_box((lo,hi),self.grip.cut_for_edge(edge)));use=e==edge;d[use],g[use]=reduced.distance(p[use])
    yield e,t,w,d,g

class ScrewCover(NipPads):
 def __init__(self,underhead,length,diameter,head_diameter,head_height):
  x,y,z=underhead;r=diameter/2;h=head_diameter/2
  self.boxes=[([x-r,y-length,z-r],[x+r,y,z+r]),([x-h,y,z-h],[x+h,y+head_height,z+h])]
  self.grip=None

class FeederContact:
 def __init__(self,base,z,auxiliary=(),feeder=None):self.base=base;self.nip_pads=NipPads(feeder);self.fixed=[Pulley(32,230),Pulley(64,230),Fairlead(),self.nip_pads,*auxiliary];self.moving=Pulley(48,z)
 def edge_contact_terms(self,q,rest,counts,radius):
  yield from self.base.edge_contact_terms(q,rest,counts,radius)
  for pulley in self.fixed+[self.moving]:yield from pulley.edge_contact_terms(q,rest,counts,radius)
 def clipped_distance(self,p,ceiling,edge_ids=None):
  # Components outside an expanded enclosing AABB cannot lower this cutoff.
  # Exact SDF values are retained for every potentially closer component.
  cutoff=np.broadcast_to(np.asarray(ceiling,dtype=float),(len(p),));d=cutoff.copy()
  for idx,value,_ in self.base.sparse_components(p,float(np.max(cutoff))):
   d[idx]=np.minimum(d[idx],value)
  for part in self.fixed+[self.moving]:
   values=part.distance_for_edges(p,edge_ids)if edge_ids is not None and hasattr(part,'distance_for_edges')else part.distance(p)
   d=np.minimum(d,values[0])
  return d
 def distance_for_edges(self,p,edge_ids):
  d,g=self.base.distance(p)
  for part in self.fixed+[self.moving]:
   x,n=part.distance_for_edges(p,edge_ids)if hasattr(part,'distance_for_edges')else part.distance(p)
   mask=x<d;d[mask]=x[mask];g[mask]=n[mask]
  return d,g
 def distance(self,p):
  d,g=self.base.distance(p)
  for pulley in self.fixed+[self.moving]:
   x,n=pulley.distance(p);mask=x<d;d[mask]=x[mask];g[mask]=n[mask]
  return d,g

def feeder_potential(z,feeder,mode='LOW'):
 if not feeder['moving_center_z_range'][0]<z<feeder['moving_center_z_range'][1]:raise ValueError('Feeder travel boundary reached')
 main=feeder['main_total_mass_g'];mc=feeder['counterweight_mass_g']if mode=='LOW'else 0.;g=feeder['cord_geometry'];radius=feeder['pulley_groove_radius']+feeder['rope_d']/2
 anchor=z+g['main_eye_above_center_mm']if mode=='LOW'else feeder['park_anchor'][2]
 zc=counter_center(anchor,feeder['rope_geometric_length_mm'],radius,g)
 # Exact implicit derivative of constant finite-radius cord length.
 def leg_derivative(anchor):
  h=g['idler_height_mm']-anchor;a=g['end_horizontal_offset_mm'];d2=a*a+h*h;ell=np.sqrt(d2-radius*radius);return -(h*ell+radius*a)/d2
 dzc=-leg_derivative(anchor)/leg_derivative(zc+g['counter_eye_above_center_mm'])if mode=='LOW'else 0.
 return .00980665*(main*z+mc*zc),.00980665*(main+mc*dzc),zc

def upstream_route(guide,axis,subdiv=8,axial_entries=True):
 # Manually threaded initial centerline. Long guide bore and real groove plane.
 points=[np.asarray(guide)];labels=[]
 def line(end,step=12):
  start=points[-1].copy();n=max(1,int(np.ceil(np.linalg.norm(end-start)/step)));points.extend(np.linspace(start,end,n+1)[1:])
 line(guide-175*axis)
 if axial_entries:line(np.array([109.,406.,238.]))
 line(np.array([102.,406.,238.]))
 rho=8.3/np.cos(np.pi/(2*subdiv));delta=np.arctan2(70,16)-np.arccos(2*rho/np.hypot(16,70))
 def arc(x,z,a,b):
  vals=np.linspace(a,b,max(2,int(np.ceil(abs(b-a)/(np.pi/subdiv)))+1));path=np.array([[x+rho*np.cos(t),406,z+rho*np.sin(t)]for t in vals]);line(path[0]);points.extend(path[1:])
 arc(64,230,np.pi/2,np.pi+delta);arc(48,160,delta,-np.pi-delta);arc(32,230,-delta,np.pi/2)
 if axial_entries:line(np.array([24.,406.,238.8]))
 line(np.array([16.,406.,238.8]))
 return np.asarray(points)
