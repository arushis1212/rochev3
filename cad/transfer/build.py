"""Parametric guided loop-transfer research subassembly."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from cad.r5m2 import build as base
from cad.r5m2.export_contact import wire_points
from cad.transfer.interfaces import add_interfaces,motion_kind,resets_with_shuttle
cq=base.cq;ROOT=base.ROOT
C=json.loads((ROOT/'spec/transfer_candidate.json').read_text());T=base.T
OUT=ROOT/'cad/transfer/generated'
def parts():
    t=T['body_thickness'];body=base.hook_body()
    # Remove the old vertical heel; straight slope meets the retained floor.
    cut=cq.Workplane('XY',origin=(0,0,-t)).polyline([(C['heel_start_u'],T['body_top']),(C['heel_floor_u'],T['pocket_bottom']),(T['pocket_right']-1,T['pocket_bottom']),(T['pocket_right']-1,T['body_top']+1),(C['heel_start_u'],T['body_top']+1)]).close().extrude(2*t)
    body=body.cut(cut)
    edges=[e for e in body.edges('|Z').vals() if abs(e.Center().x-C['heel_start_u'])<1e-6 or (abs(e.Center().x-C['heel_floor_u'])<1e-6 and abs(e.Center().y-T['pocket_bottom'])<1e-6)]
    body=body.newObject(edges).fillet(C['heel_radius'])
    front=T['gate_front_closed'];y=T['gate_bottom'];h=T['gate_thickness'];w=T['gate_width'];back=T['gate_back']
    blade=cq.Workplane('XY',origin=(0,0,-w/2)).polyline([(back,y),(front,y),(front,y+C['gate_tip_thickness_mm']),(front-C['gate_bevel_length_mm'],y+h),(back,y+h)]).close().extrude(w)
    tip_edges=[e for e in blade.edges('|Z').vals() if abs(e.Center().x-front)<1e-7 or (abs(e.Center().x-(front-C['gate_bevel_length_mm']))<1e-7 and abs(e.Center().y-(y+h))<1e-7)]
    blade=blade.newObject(tip_edges).fillet(C['gate_profile_radius_mm'])
    tail=base.box(back,T['gate_tail_front'],y,y+h,-T['gate_tail_width']/2,T['gate_tail_width']/2)
    gate=blade.union(tail).cut(base.cyl_y(y-1,y+h+1,T['gate_tail_hole_d']/2,T['gate_tail_hole_u']))
    v0,v1=C['stripper_outer_v_mm'];w0,w1=C['stripper_outer_w_mm'];u0=C['stripper_channel_mm']/2;th=C['stripper_plate_thickness_mm'];slot=C['stripper_slot_halfwidth_mm']
    def plate(a,b):
        p=base.box(a,b,v0,v1,w0,w1).cut(base.box(a-1,b+1,C['stripper_slot_bottom_v_mm'],v1+1,-slot,slot))
        p=p.edges('|X').fillet(C['stripper_edge_radius_mm'])
        rad=C['lift_pin_radius_mm']+C['lift_slot_clearance_mm'];lo=C['lift_park_v_mm'];hi=C['lift_high_v_mm']
        for w in [-C['lift_pin_w_mm'],C['lift_pin_w_mm']]:
            slotcut=base.box(a-1,b+1,lo,hi,w-rad,w+rad).union(base.cyl_x(a-1,b+1,rad,lo,w)).union(base.cyl_x(a-1,b+1,rad,hi,w))
            p=p.cut(slotcut)
        for w in [-C['anchor_bolt_w_mm'],C['anchor_bolt_w_mm']]:p=p.cut(base.cyl_x(a-1,b+1,C['anchor_bolt_clearance_mm']/2,C['anchor_bolt_v_mm'],w))
        return p
    parts={'H01_hook_body':body,'H02_gate':gate,'H02_contact_blade':blade,'R01_front_stripper':plate(u0,u0+th),'R02_rear_stripper':plate(-u0-th,-u0)}
    a=u0+th+C['lift_carriage_plate_gap_mm'];b=a+C['lift_pin_embed_mm'];v=C['lift_park_v_mm'];pinw=C['lift_pin_w_mm'];col=C['lift_carriage_column_width_mm']/2;top0,top1=C['lift_carriage_top_offsets_mm'];rod_u=(a+b)/2+C['lift_guide_u_offset_mm'];rodw=C['lift_guide_w_mm']
    carriage=base.box(a,b,v+top0,v+top1,-rodw-3,rodw+3)
    for w in [-pinw,pinw]:
        carriage=carriage.union(base.box(a,b,v-col,v+top0,w-col,w+col))
        carriage=carriage.cut(base.cyl_x(a-1,b+1,C['lift_pin_radius_mm'],v,w))
    lo,hi=C['lift_bushing_v_offsets_mm']
    for w in [-rodw,rodw]:
        carriage=carriage.union(base.cyl_y(v+lo,v+hi,C['lift_bushing_outer_d_mm']/2,rod_u,w))
        carriage=carriage.cut(base.cyl_y(v+lo-1,v+hi+1,C['lift_bushing_bore_d_mm']/2,rod_u,w))
    vlo,vhi=C['anchor_v_bounds_mm'];anchor=base.box(u0+th,u0+th+C['anchor_depth_mm'],vlo,vhi,-rodw-3,rodw+3)
    spacer=base.box(-u0,u0,vlo,vhi,-rodw+1,rodw-1)
    for w in [-C['anchor_bolt_w_mm'],C['anchor_bolt_w_mm']]:
        hole=base.cyl_x(-u0-th-1,u0+th+C['anchor_depth_mm']+1,C['anchor_bolt_clearance_mm']/2,C['anchor_bolt_v_mm'],w)
        anchor=anchor.cut(hole);spacer=spacer.cut(hole)
    for i,w in enumerate([-rodw,rodw]):
        low,high=C['lift_guide_v_bounds_mm'];anchor=anchor.cut(base.cyl_y(vlo-1,high,C['lift_guide_radius_mm'],rod_u,w))
        parts['R08_guide_rod_'+str(i)]=base.cyl_y(low,high,C['lift_guide_radius_mm'],rod_u,w)
    for i,w in enumerate([-pinw,pinw]):parts['R03_lift_pin_'+str(i)]=base.cyl_x(-u0-th-C['lift_pin_protrusion_mm'],b,C['lift_pin_radius_mm'],v,w)
    parts.update(R05_lift_carriage=carriage,R06_anchor=anchor,R07_plate_spacer=spacer)
    for i,w in enumerate([-C['anchor_bolt_w_mm'],C['anchor_bolt_w_mm']]):
        head=(u0+th+C['anchor_depth_mm'],C['anchor_bolt_v_mm'],w)
        rear=(-u0-th,C['anchor_bolt_v_mm'],w)
        parts['R09_anchor_screw_'+str(i)]=cq.Workplane(obj=base.place(base.bolt(3,C['anchor_bolt_length_mm']),head,(0,0,1),(1,0,0)))
        parts['R10_anchor_nut_'+str(i)]=cq.Workplane(obj=base.place(base.nut(3).rotate((0,0,0),(0,0,1),C['anchor_nut_rotation_deg']),rear,(0,0,1),(-1,0,0)))
    parts=add_interfaces(base,C,parts)
    I=json.loads((ROOT/'spec/transfer_interfaces.json').read_text())
    if 'verge_relief_global_box_mm' in I:
        # Convert a world-fixed nominal clearance pocket to the authored local frame.
        import math
        angle=math.radians(T['inclination_deg']);u=(0,math.cos(angle),-math.sin(angle));tip=(136,167.6794919243,114);origin=(tip[0],tip[1]-5*u[1],tip[2]-5*u[2])
        loc=cq.Location(cq.Plane(origin=origin,xDir=u,normal=(1,0,0)))
        cut=base.box(*I['verge_relief_global_box_mm']).val().moved(loc.inverse).rotate((0,0,0),(1,0,0),-20)
        parts['R05_lift_carriage']=parts['R05_lift_carriage'].cut(cq.Workplane(obj=cut))
        if 'bank_relief_global_box_mm' in I:
            cut=base.box(*I['bank_relief_global_box_mm']).val().moved(loc.inverse).rotate((0,0,0),(1,0,0),-20)
            parts['R06_anchor']=parts['R06_anchor'].cut(cq.Workplane(obj=cut))
    return parts
def main():
    OUT.mkdir(exist_ok=True,parents=True);ps=parts();profiles={};manifest={}
    for name,p in ps.items():
        bb=p.val().BoundingBox();manifest[name]={'valid':p.val().isValid(),'volume_mm3':p.val().Volume(),'bbox_mm':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax]}
        if name not in ['H01_hook_body','H02_contact_blade','R01_front_stripper','R02_rear_stripper','R03_lift_pin_0','R03_lift_pin_1']:continue
        normal,axes=(0,(1,2)) if name.startswith('R') else (2,(0,1))
        face=max([f for f in p.faces().vals() if f.normalAt().toTuple()[normal]>.999],key=lambda f:f.Area())
        bounds=[(bb.xmin,bb.xmax),(bb.ymin,bb.ymax),(bb.zmin,bb.zmax)]
        profiles['H02_gate' if name=='H02_contact_blade' else name]={'outer':wire_points(face.outerWire(),axes,.001),'holes':[wire_points(x,axes,.001) for x in face.innerWires()],'profile_axes':axes,'extrusion_axis':normal,'extrusion_bounds_mm':bounds[normal]}
    for name,p in ps.items():
        cq.exporters.export(p,str(OUT/(name+'.step')));cq.exporters.export(p,str(OUT/(name+'.stl')),tolerance=.03,angularTolerance=.1)
    modeled={'H01_hook_body','H02_gate','H02_contact_blade','R01_front_stripper','R02_rear_stripper','R03_lift_pin_0','R03_lift_pin_1'}
    auxiliary={name:{'bbox_mm':value['bbox_mm'],'motion':motion_kind(name),'resettable':resets_with_shuttle(name),'moves_with_lift':motion_kind(name)=='lift'} for name,value in manifest.items() if name not in modeled}
    from cad.transfer.contact_envelopes import carriage_boxes
    auxiliary['R05_lift_carriage']['boxes_mm']=carriage_boxes(C,json.loads((ROOT/'spec/transfer_interfaces.json').read_text()))
    for n,d in [('manifest.json',manifest),('contact_profiles.json',profiles),('auxiliary_envelopes.json',auxiliary)]: (OUT/n).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
