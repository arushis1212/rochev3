"""Physical single-station transfer installation and reusable rigid scene."""
from pathlib import Path
import json,math
from functools import lru_cache
import numpy as np
from cad.r5m2 import build as base
from cad.transfer.build import parts as transfer_parts
from cad.transfer.interfaces import motion_kind,motion_shift
I=json.loads((base.ROOT/'spec/transfer_installation.json').read_text())

def reference_frame():
 a=math.radians(I['head_inclination_deg']);u=np.array([0,math.cos(a),-math.sin(a)]);ref=np.array(I['reference_tip_xyz_mm']);return ref,u,ref-5*u

def transfer_to_world(shape):
 ref,u,origin=reference_frame();shape=shape.rotate((0,0,0),(1,0,0),I['transfer_roll_deg'])
 return base.transformed({'part':shape},tuple(origin),tuple(u),(1,0,0))['part']

@lru_cache(maxsize=1)
def mount_parts():
 cq=base.cq
 plate=base.box(*I['mount_plate_u_mm'],*I['mount_plate_v_mm'],*I['mount_plate_w_mm'])
 bracket=cq.Workplane(obj=transfer_to_world(plate.val()))
 for key in ['mount_beam_xyz_bounds_mm','mount_return_arm_xyz_bounds_mm','mount_post_xyz_bounds_mm','mount_rear_plate_xyz_bounds_mm']:bracket=bracket.union(base.box(*I[key]))
 for w,d in [(-7,I['frame_port_clearance_mm']),(7,I['frame_port_clearance_mm']),(0,I['lift_stop_head_access_d_mm'])]:
  bore=base.cyl_x(40,80,d/2,I['frame_port_v_mm'],w);bracket=bracket.cut(cq.Workplane(obj=transfer_to_world(bore.val())))
 for z in base.S['support_bank']['knockover_mount_holes_z']:bracket=bracket.cut(base.cyl_y(169,202,I['frame_port_clearance_mm']/2,I['post_x_mm'],z))
 if 'bank_relief_global_box_mm' in I:bracket=bracket.cut(base.box(*I['bank_relief_global_box_mm']))
 items={'M01_frame_bracket':bracket.val()}
 for j,w in enumerate([-7,7]):
  bolt=base.place(base.bolt(3,I['fork_mount_screw_length_mm']),(I['fork_mount_screw_seat_u_mm'],I['frame_port_v_mm'],w),(0,0,1),(-1,0,0))
  nut=base.place(base.nut(3),(I['fork_mount_nut_front_u_mm'],I['frame_port_v_mm'],w),(0,0,1),(1,0,0))
  items[f'M02_fork_screw_{j}']=transfer_to_world(bolt);items[f'M03_fork_nut_{j}']=transfer_to_world(nut)
 return items

def installed(ps,tp,advance,gate,lift,guide,tip=None,roll=None,reset=0.,feed_mode='high',carrier_z=160,clamp_pose=None):
 ref,u,origin=reference_frame();tip=ref+advance*u if tip is None else np.array(tip);roll=I['transfer_roll_deg'] if roll is None else roll
 scene=base.integrated_instances(ps,head_tip=tip.tolist(),guide_tip=guide,head_gate=gate,head_roll=roll,support_q=I['support_q_mm'],support_gate_q=I['support_gate_q_mm'],takedown_z=I['take_down_z_mm'],feed_mode=feed_mode,carrier_z=carrier_z)
 length=I['fairlead_mount_screw_length_mm'];scene.pop('HW_M3x16_eye')
 scene[f'HW_M3x{length}_eye']=base.place(base.bolt(3,length),I['fairlead_mount_screw_underhead_xyz_mm'],(1,0,0),(0,1,0))
 for source,dest in [('H01_hook_body','H01_hook_body'),('H02_gate','H02_gate'),('TH_H03_barrel_stop','H03_barrel_stop')]:
  solid=tp[source].val()
  if source=='H02_gate':solid=solid.translate((-gate,0,0))
  solid=solid.rotate((0,0,0),(1,0,0),roll)
  scene['TOOL_'+dest]=base.transformed({'p':solid},tuple(tip-5*u),tuple(u),(1,0,0))['p']
 for name,obj in tp.items():
  if name.startswith('R'):scene['TRANSFER_'+name]=transfer_to_world(obj.val().translate(motion_shift(name,advance,gate,lift,reset)))
 scene.update(mount_parts())
 for j,z in enumerate(base.S['support_bank']['knockover_mount_holes_z']):
  scene[f"HW_M3x16_knockover_{I['post_index']}_{j}"]=base.place(base.bolt(3,I['post_mount_screw_length_mm']),(I['post_x_mm'],170,z),(1,0,0),(0,-1,0))
  scene[f"HW_M3nut_knockover_{I['post_index']}_{j}"]=base.place(base.nut(3),(I['post_x_mm'],I['post_mount_nut_y_mm'],z),(1,0,0),(0,1,0))
 if clamp_pose is not None:
  center,angles=clamp_pose;scale=base.S['cloth_clamp']['angular_scale_mm'];yaw,pitch,roll=np.asarray(angles)*180/math.pi/scale
  for name,shape in list(scene.items()):
   if name.startswith(('D01_','D02_','D03_','D04_','HW_M3x16_cloth_','HW_M3nut_cloth_')):
    shape=shape.translate((-150,-165,-I['take_down_z_mm']))
    shape=shape.rotate((0,0,0),(1,0,0),float(roll)).rotate((0,0,0),(0,1,0),float(-pitch)).rotate((0,0,0),(0,0,1),float(yaw))
    scene[name]=shape.translate(tuple(center))
 return scene

def cases():
 park=I['guide_park_xyz_mm'];ref,u,_=reference_frame()
 rows=[(n,a,g,h,park,None,I['transfer_roll_deg']) for n,a,g,h in [('park',0,16.5,0),('extended',8.75,16.5,0),('lifted',8.75,16.5,6),('closed',8.75,0,6),('withdrawn',-8.5,0,6)]]
 phases=[{'id':key} for key in I['guide_local_waypoints_mm']]+[p for p in base.S['handoff_trial']['phases'] if p['id']=='S8_head_clear']
 for p in phases:
  if p['id'] in I['guide_local_waypoints_mm']:
   a=math.radians(I['head_inclination_deg']);r=math.radians(I['transfer_roll_deg']);v=np.array([math.sin(r),math.sin(a)*math.cos(r),math.cos(a)*math.cos(r)]);w=np.array([math.cos(r),-math.sin(a)*math.sin(r),-math.cos(a)*math.sin(r)])
   origin=ref-5*u;lu,lv,lw=I['guide_local_waypoints_mm'][p['id']];g=origin+lu*u+lv*v+lw*w
   rows.append((p['id'],8.75,16.5,6,g.tolist(),None,20))
  if p['id']=='S8_head_clear':rows.append((p['id'],0,0,6,p['guide_tip'],p['head_tip'],p['head_roll']))
 return rows

def main():
 out=base.ROOT/'cad/transfer/installed';out.mkdir(exist_ok=True);items=mount_parts();ps=base.parts();tp=transfer_parts();scene=installed(ps,tp,0,16.5,0,I['guide_park_xyz_mm']);assembly=base.cq.Assembly();manifest={}
 for name,obj in items.items():
  b=obj.BoundingBox();manifest[name]={'valid':obj.isValid(),'solids':len(obj.Solids()),'volume_mm3':obj.Volume(),'bbox_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]}
  for ext in ['step','stl']:base.cq.exporters.export(obj,str(out/(name+'.'+ext)))
 for name,obj in scene.items():assembly.add(obj,name=name)
 assembly.save(str(out/'installation.step'))
 (out/'manifest.json').write_text(json.dumps({'revision':I['revision'],'mount_parts':manifest,'assembly_solids':len(scene),'scope':'Nominal single-station physical mount candidate'},indent=2)+'\n')
 print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
