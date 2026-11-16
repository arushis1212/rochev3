"""Parametric crochet research fixture, millimetres.
Dimensions: spec/r5_m2_fixture.json. Exports OpenCascade solids, STEP and STL.
"""
from pathlib import Path
import json, math, hashlib, argparse, sys
import cadquery as cq
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from cad.r5m2 import peripherals
SPEC=ROOT/'spec/r5_m2_fixture.json'
S=json.loads(SPEC.read_text()); T=S['tool']; P=S['slide']
OUT=ROOT/'cad/r5m2/generated'

def box(x0,x1,y0,y1,z0,z1):
    return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))

def cyl_x(a,b,r,y=0,z=0):
    return cq.Workplane('YZ',origin=(a,y,z)).circle(r).extrude(b-a)

def cyl_z(a,b,r,x=0,y=0):
    return cq.Workplane('XY',origin=(x,y,a)).circle(r).extrude(b-a)

def cyl_y(a,b,r,x=0,z=0):
    return cq.Workplane('XZ',origin=(x,a,z)).circle(r).extrude(-(b-a))

def hex_z(a,b,af,x=0,y=0):
    return cq.Workplane('XY',origin=(x,y,a)).polygon(6,af/math.cos(math.pi/6)).extrude(b-a)

def hex_y(a,b,af,x=0,z=0):
    return cq.Workplane('XZ',origin=(x,a,z)).polygon(6,af/math.cos(math.pi/6)).extrude(-(b-a))

def hook_body():
    t=T['body_thickness']
    body=box(T['body_back'],T['body_tip'],T['body_bottom'],T['body_top'],-t/2,t/2)
    nose=box(T['pocket_right'],T['body_tip'],T['body_top'],T['nose_top'],-t/2,t/2)
    ramp=cq.Workplane('XY',origin=(0,0,-t)).polyline([(T['nose_ramp_start'],T['gate_bottom']+T['gate_thickness']),(T['nose_ramp_end'],T['nose_top']),(T['nose_ramp_start'],T['nose_top'])]).close().extrude(2*t)
    body=body.union(nose.cut(ramp))
    cut=box(T['pocket_left'],T['pocket_right'],T['pocket_bottom'],T['body_top']+1,-t,t)
    body=body.cut(cut)
    # Fillet just the two re-entrant mouth roots in the profile; no invented spline.
    root=[]; nose=[]
    for e in body.edges('|Z').vals():
        c=e.Center()
        if abs(c.y-T['pocket_bottom'])<1e-7: root.append(e)
    body=body.newObject(root).fillet(T['pocket_root_radius'])
    for e in body.edges('|Z').vals():
        c=e.Center()
        if abs(c.x-T['body_tip'])<1e-7: nose.append(e)
    body=body.newObject(nose).fillet(T['nose_radius'])
    body=body.cut(box(T['pocket_right']-0.1,T['nose_slot_end'],T['nose_slot_bottom'],T['nose_slot_top'],-t,t))
    for u in T['body_fix_holes_u']:
        body=body.cut(cyl_z(-t,t,T['body_fix_hole_d']/2,u,T['body_fix_hole_v']))
    return body

def gate():
    y=T['gate_bottom']; h=T['gate_thickness']; w=T['gate_width']
    g=box(T['gate_back'],T['gate_front_closed'],y,y+h,-w/2,w/2)
    g=g.union(box(T['gate_back'],T['gate_tail_front'],y,y+h,-T['gate_tail_width']/2,T['gate_tail_width']/2))
    return g.cut(cyl_y(y-1,y+h+1,T['gate_tail_hole_d']/2,T['gate_tail_hole_u']))

def barrel():
    b=cyl_x(T['barrel_back'],T['barrel_front'],T['barrel_d']/2)
    b=b.cut(box(T['barrel_back']-1,T['barrel_front']+1,T['barrel_slot_bottom'],T['barrel_slot_top'],-T['barrel_slot_width']/2,T['barrel_slot_width']/2))
    for u in T['body_fix_holes_u']:
        v=T['body_fix_hole_v']; r=T['barrel_d']/2
        b=b.cut(cyl_z(-r-1,r+1,T['body_fix_hole_d']/2,u,v))
        b=b.cut(cyl_z(r-T['barrel_bolt_counterbore_depth'],r+1,T['barrel_bolt_counterbore_d']/2,u,v))
        b=b.cut(hex_z(-r-1,-r+T['barrel_nut_depth'],T['barrel_nut_across_flats'],u,v))
    # Rear bridge and slotted positive travel stop co-rotate with the barrel.
    a=T['gate_stop_plate_back']; bnd=T['gate_stop_plate_front']; v=T['gate_stop_plate_offset_v']; w=T['gate_stop_plate_width']/2
    plate=box(a,bnd,v,v+T['gate_stop_plate_thickness'],-w,w)
    sleeve=S['tool']['stop_sleeve_od']; gap=S['tool']['stop_slot_side_clearance']
    rad=(sleeve+gap)/2; c=T['gate_tail_hole_u']; stroke=T['gate_stroke']
    slot=box(c-stroke,c,v-1,v+T['gate_stop_plate_thickness']+1,-rad,rad)
    slot=slot.union(cyl_y(v-1,v+T['gate_stop_plate_thickness']+1,rad,c-stroke)).union(cyl_y(v-1,v+T['gate_stop_plate_thickness']+1,rad,c))
    plate=plate.cut(slot)
    bridge=box(bnd-4,bnd,4,v+T['gate_stop_plate_thickness'],-w,w)
    return b.union(plate).union(bridge)

def bearing():
    a=T['bearing_back']; b=T['bearing_front']; u=(a+b)/2
    ring=cyl_x(a,b,T['bearing_outer_d']/2).cut(cyl_x(a-1,b+1,T['bearing_bore_d']/2))
    # Flat two-hole mounting pad attached to lower outside of bearing.
    v0=-T['mount_tab_offset']-T['mount_tab_height']/2
    v1=-T['mount_tab_offset']+T['mount_tab_height']/2
    pad=box(a,b,v0,v1,-T['mount_tab_width']/2,T['mount_tab_width']/2)
    ring=ring.union(pad)
    for x in (u-T['mount_hole_pitch']/2,u+T['mount_hole_pitch']/2):
        ring=ring.cut(cyl_y(v0-1,v1+1,T['mount_hole_d']/2,x))
        ring=ring.cut(hex_y(v1-3.4,v1+1,P['nut_af'],x))
        ring=ring.cut(box(x-T['bearing_nut_access_width']/2,x+T['bearing_nut_access_width']/2,v1-3.4,v1,0,T['mount_tab_width']/2+1))
    # Radial roll clamp has a trapped nut and side insertion window.
    u=(a+b)/2; lo,hi=T['roll_lock_nut_v']; hw=T['roll_lock_boss_width']/2
    ring=ring.union(box(u-T['roll_lock_boss_length']/2,u+T['roll_lock_boss_length']/2,8,T['roll_lock_boss_top_v'],-hw,hw))
    ring=ring.cut(cyl_x(a-1,b+1,T['bearing_bore_d']/2))
    ring=ring.cut(cyl_y(7,T['roll_lock_boss_top_v']+1,P['bolt_clearance']/2,u))
    ring=ring.cut(hex_y(lo,hi,P['nut_af'],u)).cut(box(u-3.4,u+3.4,lo,hi,0,hw+1))
    return ring

def collar(a):
    c=cyl_x(a,a+T['collar_thickness'],T['collar_d']/2).cut(cyl_x(a-1,a+T['collar_thickness']+1,T['collar_bore_d']/2))
    # Split collar, transverse M3 clamp through ears. Tool-free roll lock is separate.
    c=c.cut(box(a-1,a+T['collar_thickness']+1,0,T['collar_d'], -0.5,0.5))
    ears=box(a,a+T['collar_thickness'],7,15,-T['collar_ear_half_width'],T['collar_ear_half_width']).cut(box(a-1,a+T['collar_thickness']+1,0,16,-0.5,0.5))
    c=c.union(ears)
    c=c.cut(cyl_x(a-1,a+T['collar_thickness']+1,T['collar_bore_d']/2))
    return c.cut(cyl_z(-T['collar_ear_half_width']-1,T['collar_ear_half_width']+1,T['collar_fix_d']/2,a+T['collar_thickness']/2,12))

def gate_knob():
    u=T['gate_tail_hole_u']; v=T['gate_bottom']; l=T['gate_knob_length']; w=T['gate_knob_width']; h=T['gate_knob_height']
    b=box(u-l/2,u+l/2,v-h,v,-w/2,w/2)
    b=b.cut(cyl_y(v-h-1,v+1,T['gate_knob_hole_d']/2,u))
    return b.cut(hex_y(v-h-1,v-h+T['gate_knob_nut_pocket_depth'],T['barrel_nut_across_flats'],u))

def stop_sleeve():
    a=T['gate_bottom']+T['gate_thickness']; b=T['gate_stop_plate_offset_v']+T['gate_stop_plate_thickness']+T['stop_axial_clearance']
    return cyl_y(a,b,T['stop_sleeve_od']/2,T['gate_tail_hole_u']).cut(cyl_y(a-1,b+1,T['stop_sleeve_id']/2,T['gate_tail_hole_u']))

def slide_base(L):
    w=P['outside_width']/2; c=P['channel_width']/2; f=P['floor_thickness']; h=P['wall_top']
    b=box(-L/2,L/2,-w,w,0,f)
    b=b.union(box(-L/2,L/2,-w,-c,f,h)).union(box(-L/2,L/2,c,w,f,h))
    # Recessed stack mounting screws don't obstruct the moving carriage.
    pitch=P['mount_hole_pitch']/2
    for u,v in ((pitch,0),(-pitch,0),(0,pitch),(0,-pitch)):
        b=b.cut(cyl_z(-1,f+1,P['bolt_clearance']/2,u,v))
        b=b.cut(cyl_z(f-P['counterbore_depth'],f+1,P['counterbore_d']/2,u,v))
    for x in (-L/2+P['cap_bolt_end_inset'],L/2-P['cap_bolt_end_inset']):
        for y in (-P['cap_bolt_y'],P['cap_bolt_y']):
            b=b.cut(cyl_z(-1,h+1,P['bolt_clearance']/2,x,y))
            b=b.cut(hex_z(-1,P['cap_nut_pocket_roof'],P['nut_af'],x,y))
    for sign in (-1,1):
        x=sign*(L/2-P['endstop_thickness']/2)
        for y in (-P['endstop_hole_y'],P['endstop_hole_y']):
            b=b.cut(cyl_z(-1,f+1,P['bolt_clearance']/2,x,y))
            b=b.cut(hex_z(-1,P['endstop_nut_roof'],P['nut_af'],x,y))
    # Side lock with captive nut, not a screw threaded directly into PLA.
    b=b.cut(cyl_y(c-1,w+1,P['bolt_clearance']/2,0,f+P['carriage_flange_height']/2))
    b=b.cut(hex_y(P['lock_nut_inner_y'],P['lock_nut_outer_y'],P['nut_af'],0,f+P['carriage_flange_height']/2))
    b=b.cut(box(-P['lock_nut_access_width']/2,P['lock_nut_access_width']/2,P['lock_nut_inner_y'],P['lock_nut_outer_y'],f+P['carriage_flange_height']/2,h+0.1))
    return b

def slide_carriage():
    a=P['carriage_length']/2; w=P['carriage_width']/2; f=P['floor_thickness']; h=f+P['carriage_flange_height']
    c=box(-a,a,-w,w,f,h).union(box(-a,a,-P['neck_width']/2,P['neck_width']/2,h,P['carriage_top']))
    for x in (-P['mount_hole_pitch']/2,P['mount_hole_pitch']/2):
        c=c.cut(cyl_z(f-1,P['carriage_top']+1,P['bolt_clearance']/2,x))
        c=c.cut(hex_z(f-1,P['nut_pocket_roof'],P['nut_af'],x))
    return c

def slide_cap(L,sign):
    inn=P['cap_inner_edge']; out=P['outside_width']/2; z=P['wall_top']
    b=box(-L/2,L/2,inn if sign>0 else -out,out if sign>0 else -inn,z,z+P['cap_thickness'])
    for x in (-L/2+P['cap_bolt_end_inset'],L/2-P['cap_bolt_end_inset']):
        b=b.cut(cyl_z(z-1,z+P['cap_thickness']+1,P['bolt_clearance']/2,x,sign*P['cap_bolt_y']))
        b=b.cut(cyl_z(z+P['cap_thickness']-P['cap_counterbore_depth'],z+P['cap_thickness']+1,P['cap_counterbore_d']/2,x,sign*P['cap_bolt_y']))
    return b

def slide_stop(L,sign):
    x=sign*(L/2-P['endstop_thickness']/2)
    b=box(x-P['endstop_thickness']/2,x+P['endstop_thickness']/2,-P['channel_width']/2,P['channel_width']/2,P['floor_thickness'],P['endstop_top'])
    for sign_y in (-1,1):
        inn=P['cap_inner_edge']-P['stop_cap_clearance']; out=P['channel_width']/2+1
        b=b.cut(box(x-P['endstop_thickness'],x+P['endstop_thickness'],inn if sign_y>0 else -out,out if sign_y>0 else -inn,P['wall_top']-P['stop_cap_clearance'],P['endstop_top']+1))
    for y in (-P['endstop_hole_y'],P['endstop_hole_y']):
        b=b.cut(cyl_z(P['floor_thickness']-1,P['endstop_top']+1,P['bolt_clearance']/2,x,y))
        b=b.cut(cyl_z(P['endstop_top']-P['counterbore_depth'],P['endstop_top']+1,P['counterbore_d']/2,x,y))
    return b

def guide_tube():
    g=S['guide']; r=g['tube_od']/2
    return cyl_x(-g['tube_length'],g.get('inner_tube_front',0),r).cut(cyl_x(-g['tube_length']-1,1,r-g['tube_wall']))

def guide_insert():
    g=S['guide'];a=g['exit_insert_back'];b=g['exit_insert_front'];r=g['exit_insert_od']/2
    return cyl_x(a,b,r).cut(cyl_x(a-1,b+1,r-g['exit_insert_wall']))

def guide_reducer():
    g=S['guide']; a=g['reducer_back']; b=g['reducer_front']; r=g['reducer_od']/2
    return cyl_x(a,b,r).cut(cyl_x(a-1,b+1,r-g['reducer_wall']))

def guide_mount():
    g=S['guide']; a,b,c=g['mount_block']; start=g['mount_back_u']; u=start+a/2
    block=box(start,start+a,-b/2,b/2,-c/2,c/2).cut(cyl_x(start-1,start+a+1,g['mount_bore']/2))
    lo,hi=g['outer_lock_nut_v']
    block=block.cut(cyl_y(0,b/2+1,g['tube_lock_hole_d']/2,u)).cut(hex_y(lo,hi,P['nut_af'],u))
    block=block.cut(box(u-3.4,u+3.4,lo,hi,0,c/2+1))
    for x in (u-g['mount_hole_pitch']/2,u+g['mount_hole_pitch']/2):
        block=block.cut(cyl_z(-c/2-1,c/2+1,g['mount_hole_d']/2,x,g['mount_hole_offset_v']))
    return block

def guide_outer():
    g=S['guide']; a=g['outer_tube_back']; b=g['outer_tube_front']; r=g['outer_tube_od']/2
    return cyl_x(a,b,r).cut(cyl_x(a-1,b+1,r-g['outer_tube_wall']))

def guide_bush(rear=False):
    g=S['guide']; a=g['rear_bushing_back'] if rear else g['front_bushing_back']; b=a+g['bushing_length']
    part=cyl_x(a,b,g['bushing_od']/2)
    return part.cut(cyl_x(a-g['rear_flange_length']-1,b+1,g['bushing_bore']/2))

def guide_frame():
    th=math.radians(S['guide']['inclination_deg']); co=math.cos(th); si=math.sin(th)
    return co,si,(0,-co,-si),(0,-si,co)

def guide_adapter():
    F=S['frame']; g=S['guide']; co,si,eu,ew=guide_frame(); x0=-F['guide_lateral_offset']-16; x1=F['guide_shelf_width']+x0
    shelf=box(*F['guide_shelf_local_u'],-16,x1+F['guide_lateral_offset'],-16,-8)
    for u in (-153,-137):
        shelf=shelf.cut(cyl_z(-17,-7,P['bolt_clearance']/2,u,g['mount_hole_offset_v']))
        shelf=shelf.cut(hex_z(-17,-12,P['nut_af'],u,g['mount_hole_offset_v']))
    origin=(-F['guide_lateral_offset'],-172*co,-145*si)
    shelf=cq.Workplane().newObject([place(shelf,origin,eu,ew)])
    shelf=shelf.cut(box(-100,100,-4,50,-100,100))
    b=box(F['guide_vertical_left_x'],x1,-12,-4,*F['guide_vertical_z']).union(shelf)
    bore=cyl_x(-185,-150,g['adapter_feed_bore']/2)
    b=b.cut(cq.Workplane().newObject([place(bore,origin,eu,ew)]))
    for z in (-8,8):
        b=b.cut(cyl_y(-20,-3,P['bolt_clearance']/2,0,z))
        b=b.cut(cyl_y(-20,-7.5,F['adapter_counterbore_d']/2,0,z))
    return b

def support_carriage():
    B=S['support_bank']; f=B['bank_floor']; a=B['bank_carriage_length']/2
    c=box(-a,a,-P['carriage_width']/2,P['carriage_width']/2,f,f+P['carriage_flange_height'])
    c=c.union(box(-a,a,-P['neck_width']/2,P['neck_width']/2,f+P['carriage_flange_height'],B['bank_carriage_top']))
    c=c.union(box(B['index_arm_start_u'],B['index_arm_end_u'],-B['index_arm_width']/2,B['index_arm_width']/2,B['bank_carriage_top'],B['bank_carriage_top']+B['index_arm_height']))
    c=c.cut(cyl_z(f-1,B['bank_carriage_top']+B['index_arm_height']+1,B['index_pin_bore']/2,B['index_arm_u']))
    for u in (-P['mount_hole_pitch']/2,P['mount_hole_pitch']/2):
        c=c.cut(cyl_z(f-1,B['bank_carriage_top']+1,P['bolt_clearance']/2,u))
        c=c.cut(hex_z(f-1,B['bank_carriage_top']-5.5,P['nut_af'],u))
    return c

def support_bed():
    B=S['support_bank']; ox,oy,oz=B['bank_origin']; W=B['bank_width']; L=B['bank_length']; f=B['bank_floor']; h=B['bank_top']
    b=box(ox-W/2,ox+W/2,oy-L/2,oy+L/2,oz,oz+h)
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']
        b=b.cut(box(x-P['channel_width']/2,x+P['channel_width']/2,oy-L/2-1,oy+L/2+1,oz+f,oz+h+1))
    # End ties fit into relieved rails; they are separate parts, not overlapping solids.
    for sign in (-1,1):
        y=oy+sign*(L/2-P['endstop_thickness']/2); e=B['cover_bed_relief_clearance']
        b=b.cut(box(ox-W/2-1,ox+W/2+1,y-P['endstop_thickness']/2-e,y+P['endstop_thickness']/2+e,oz+f,oz+h+1))
    for x in B['bank_cap_bolt_x']:
        for y in B['bank_cap_bolt_y']:
            b=b.cut(cyl_z(oz-1,oz+h+1,S['fasteners']['M2']['clearance']/2,x,y))
            b=b.cut(hex_z(oz-1,oz+4.4,T['barrel_nut_across_flats'],x,y))
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']
        for q in B['index_offsets_y']: b=b.cut(cyl_z(oz-1,oz+h+1,B['index_pin_bore']/2,x,oy+q+B['index_arm_u']))
    for x,y in B['bank_mount_holes']:
        b=b.cut(cyl_z(oz-1,oz+f+1,P['bolt_clearance']/2,x,y))
        b=b.cut(cyl_z(oz+f-P['counterbore_depth'],oz+f+1,P['counterbore_d']/2,x,y))
    return b

def support_cap():
    B=S['support_bank']; ox,oy,oz=B['bank_origin']; W=B['bank_width']; L=B['bank_length']; z=oz+B['bank_top']
    b=box(ox-W/2,ox+W/2,oy-L/2,oy+L/2,z,z+B['bank_cap_thickness'])
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']; hw=B['bank_cap_slot_width']/2
        b=b.cut(box(x-hw,x+hw,oy-L/2-1,oy+L/2+1,z-1,z+B['bank_cap_thickness']+1))
    # End ties keep the cover one part; they are also positive carriage end stops.
    for sign in (-1,1):
        y=oy+sign*(L/2-P['endstop_thickness']/2)
        b=b.union(box(ox-W/2,ox+W/2,y-P['endstop_thickness']/2,y+P['endstop_thickness']/2,oz+B['bank_floor'],z+B['bank_cap_thickness']))
    for x in B['bank_cap_bolt_x']:
        for y in B['bank_cap_bolt_y']:
            b=b.cut(cyl_z(oz+B['bank_floor']-1,z+B['bank_cap_thickness']+1,S['fasteners']['M2']['clearance']/2,x,y))
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']
        for q in B['index_offsets_y']: b=b.cut(cyl_z(oz-1,z+B['bank_cap_thickness']+1,B['index_pin_bore']/2,x,oy+q+B['index_arm_u']))
    return b

def support_holder():
    B=S['support_bank']; a=B['clamp_back_u']; e=B['clamp_front_u']; w=B['clamp_width']/2
    b=box(a,e,B['clamp_bottom_v'],B['clamp_top_v'],-w,w)
    for off in (-B['pair_centers']/2,B['pair_centers']/2):
        b=b.cut(box(a-1,e+1,T['barrel_slot_bottom'],T['barrel_slot_top'],off-T['barrel_slot_width']/2,off+T['barrel_slot_width']/2))
    for u in T['body_fix_holes_u']:
        if not a<u<e: continue
        b=b.cut(cyl_z(-w-1,w+1,T['body_fix_hole_d']/2,u,T['body_fix_hole_v']))
        b=b.cut(hex_z(-w-1,-w+T['barrel_nut_depth'],T['barrel_nut_across_flats'],u,T['body_fix_hole_v']))
    # Pair closes through one crossbar; same stop-slot geometry as hook tool.
    v=T['gate_stop_plate_offset_v']; back=T['gate_stop_plate_back']; front=T['gate_stop_plate_front']
    plate=box(back,front,v,v+T['gate_stop_plate_thickness'],-w,w)
    rad=(T['stop_sleeve_od']+T['stop_slot_side_clearance'])/2; c=T['gate_tail_hole_u']; st=T['gate_stroke']
    for off in (-B['pair_centers']/2,B['pair_centers']/2):
        slot=box(c-st,c,v-1,v+T['gate_stop_plate_thickness']+1,off-rad,off+rad)
        for x in (c-st,c): slot=slot.union(cyl_y(v-1,v+T['gate_stop_plate_thickness']+1,rad,x,off))
        plate=plate.cut(slot)
    b=b.union(plate).union(box(front-4,front,4,v+T['gate_stop_plate_thickness'],-w,w))
    # Two bottom-access screws into captive nuts, for mounting to carriage.
    mid=(a+e)/2
    for u in (mid-P['mount_hole_pitch']/2,mid+P['mount_hole_pitch']/2):
        b=b.cut(cyl_y(B['clamp_bottom_v']-1,-3,P['bolt_clearance']/2,u))
        b=b.cut(hex_y(B['holder_nut_floor_v'],B['holder_nut_roof_v'],P['nut_af'],u))
        b=b.cut(box(u-P['nut_af']/2-0.5,u+P['nut_af']/2+0.5,B['holder_nut_floor_v'],B['holder_nut_roof_v'],0,w+1))
    return b.cut(box(*B["guide_relief_local"]))

def pair_knob():
    B=S['support_bank']; u=T['gate_tail_hole_u']; l=T['gate_knob_length']; v=T['gate_bottom']; h=T['gate_knob_height']; w=B['pair_knob_width']/2
    b=box(u-l/2,u+l/2,v-h,v,-w,w)
    for off in (-B['pair_centers']/2,B['pair_centers']/2):
        b=b.cut(cyl_y(v-h-1,v+1,T['gate_knob_hole_d']/2,u,off))
        b=b.cut(hex_y(v-h-1,v-h+T['gate_knob_nut_pocket_depth'],T['barrel_nut_across_flats'],u,off))
    return b

def knockover():
    B=S['support_bank']; cx=B['bank_origin'][0]; z=B['tool_axis_z']; W=B['knockover_width']; H=B['knockover_height']; y=B['knockover_y']
    b=box(cx-W/2,cx+W/2,y,y+B['knockover_thickness'],z-H/2,z+H/2)
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']
        hw=B['presentation_window_width']/2
        b=b.cut(box(x-hw,x+hw,y-1,y+B['knockover_thickness']+1,B['presentation_window_bottom_z'],B['presentation_window_top_z']))
        for off in (-B['pair_centers']/2,B['pair_centers']/2):
            w=B['knockover_slot_width']/2; bottom=B['knockover_slot_bottom_z']
            b=b.cut(box(x+off-w,x+off+w,y-1,y+B['knockover_thickness']+1,bottom,bottom+B['knockover_slot_height']))
    for x in B['knockover_mount_holes_x']:
        for z in B['knockover_mount_holes_z']: b=b.cut(cyl_y(y-1,y+B['knockover_thickness']+1,P['bolt_clearance']/2,x,z))
    return b

def z_bracket(guide=False):
    F=S['frame']; w=F['z_bracket_width']/2; d=F['z_bracket_depth']/2; h=F['z_bracket_height']; t=F['z_bracket_thickness']; zc=F['z_axis_center_above_xy']
    if guide: h=F['guide_z_bracket_height'];zc=F['guide_z_axis_center_above_xy']
    b=box(-w,w,-d,d,0,t).union(box(-w,w,-d,-d+t,t,h))
    for y in (-P['mount_hole_pitch']/2,P['mount_hole_pitch']/2):
        b=b.cut(cyl_z(-1,t+1,P['bolt_clearance']/2,0,y)).cut(cyl_z(t-P['counterbore_depth'],t+1,P['counterbore_d']/2,0,y))
    for z in (zc-P['mount_hole_pitch']/2,zc+P['mount_hole_pitch']/2):
        b=b.cut(cyl_y(-d-1,-d+t+1,P['bolt_clearance']/2,0,z))
    return b

def head_adapter():
    F=S['frame']; a=T['bearing_back']; b=T['bearing_front']; u=(a+b)/2; v=-T['mount_tab_offset']-T['mount_tab_height']/2
    pad=box(a,b,v-F['tool_adapter_thickness'],v,-F['tool_lateral_offset']-10,9)
    th=math.radians(T['inclination_deg']); normal=(math.cos(th),math.sin(th),0)
    plane=cq.Plane(origin=(u-8*normal[0],v-8*normal[1],-F['tool_lateral_offset']),xDir=(0,0,1),normal=normal)
    base=cq.Workplane(plane).rect(F['tool_adapter_vertical_width'],F['tool_adapter_vertical_height']).extrude(F['tool_adapter_vertical_thickness'])
    for pos in (-P['mount_hole_pitch']/2,P['mount_hole_pitch']/2):
        hole=cq.Workplane(plane).center(0,pos).circle(P['bolt_clearance']/2).extrude(F['tool_adapter_vertical_thickness']+1)
        base=base.cut(hole)
        cb=cq.Workplane(plane).workplane(offset=F['tool_adapter_vertical_thickness']-F['adapter_counterbore_depth']).center(0,pos).circle(F['adapter_counterbore_d']/2).extrude(F['adapter_counterbore_depth']+1)
        base=base.cut(cb)
    # Remove the slab behind the vertical mounting plane in the rail's X band.
    rear=cq.Workplane(plane).rect(200,200).extrude(-100)
    lateral=box(-150,50,-100,100,-100,F['head_adapter_lateral_trim_w'])
    pad=pad.cut(rear.intersect(lateral)).union(base)
    for pos in (-P['mount_hole_pitch']/2,P['mount_hole_pitch']/2):
        pad=pad.cut(cq.Workplane(plane).center(0,pos).circle(P['bolt_clearance']/2).extrude(40))
        pad=pad.cut(cq.Workplane(plane).workplane(offset=3.5).center(0,pos).circle(F['adapter_counterbore_d']/2).extrude(40))
    for x in (u-T['mount_hole_pitch']/2,u+T['mount_hole_pitch']/2):
        pad=pad.cut(cyl_y(v-F['tool_adapter_thickness']-1,v+1,P['bolt_clearance']/2,x))
    return pad

def bed_pedestal():
    B=S['support_bank']; F=S['frame']; w=B['pedestal_width']/2; d=B['pedestal_depth']/2; z=F['base_size'][2]
    b=box(-w,w,-d,d,z,z+B['pedestal_height']).cut(cyl_z(z-1,z+B['pedestal_height']+1,P['bolt_clearance']/2))
    for lo,hi in (B['pedestal_lower_nut_z'],B['pedestal_upper_nut_z']):
        b=b.cut(hex_z(lo,hi,P['nut_af'])).cut(box(0,w+1,-P['nut_af']/2-0.5,P['nut_af']/2+0.5,lo,hi))
    return b

def knockover_post():
    B=S['support_bank'];F=S['frame'];w=B['knockover_post_width']/2;yf=B['knockover_post_front_y'];yb=yf+B['knockover_post_depth'];z0=F['base_size'][2];top=B['tool_axis_z']+B['knockover_height']/2
    b=box(-w,w,yf,yb,z0,top).union(box(-w,w,B['post_arm_front_y'],yf,B['knockover_post_arm_floor_z'],top))
    b=b.union(box(-B['post_foot_width']/2,B['post_foot_width']/2,yf,yb,z0,z0+B['post_foot_height']))
    for x in (-12.,12.):b=b.cut(cyl_z(z0-1,z0+B['post_foot_height']+1,P['bolt_clearance']/2,x,(yf+yb)/2))
    lo,hi=B['post_nut_y']
    for z in B['knockover_mount_holes_z']:
        b=b.cut(cyl_y(B['knockover_y']-1,yb+1,P['bolt_clearance']/2,0,z))
        b=b.cut(hex_y(lo,hi,P['nut_af'],0,z)).cut(box(0,w+1,lo,hi,z-3.4,z+3.4))
    return b

def base_board():
    F=S['frame']; B=S['support_bank']; w,d,t=F['base_size']; b=box(0,w,0,d,0,t)
    a,z,y,w=F['cloth_opening']
    b=b.cut(box(a,z,y,w,-1,t+1))
    holes=list(B['bank_mount_holes'])+[[x,S['feeder']['base_bracket_y']] for x in S['feeder']['base_bracket_x']]
    for ox,oy,_ in (F['head_x_origin'],F['guide_x_origin']):
        holes.extend([[ox-8,oy],[ox+8,oy]])
    for cx in B['knockover_mount_holes_x']:
        holes.extend([[cx-12,(B['knockover_post_front_y']+B['knockover_post_front_y']+B['knockover_post_depth'])/2],[cx+12,(B['knockover_post_front_y']+B['knockover_post_front_y']+B['knockover_post_depth'])/2]])
    for x,y in holes: b=b.cut(cyl_z(-1,t+1,P['bolt_clearance']/2,x,y))
    for x,y in F['foot_centers']:
        b=b.cut(cyl_z(-1,t+1,P['bolt_clearance']/2,x,y))
        b=b.cut(cyl_z(t-F['foot_counterbore_depth'],t+1,P['counterbore_d']/2,x,y))
    return b

def base_foot():
    F=S['frame']; w=F['foot_width']/2; h=F['foot_height']
    return box(-w,w,-w,w,-h,0).cut(cyl_z(-h-1,1,P['bolt_clearance']/2)).cut(hex_z(-h-1,F['foot_nut_roof_z'],P['nut_af']))

def add_bank_mounts(items,ps):
    B=S['support_bank'];F=S['frame'];items['F03_base_board']=ps['F03_base_board'].val()
    for i,(x,y) in enumerate(B['bank_mount_holes']):
        items[f'B08_pedestal_{i}']=ps['B08_pedestal'].translate((x,y,0)).val()
        under=B['bank_origin'][2]+B['bank_floor']-P['counterbore_depth']
        items[f'HW_M3x12_pedestal_top_{i}']=bolt(3,12).translate((x,y,under)).val()
        items[f'HW_M3nut_pedestal_top_{i}']=nut(3).translate((x,y,B['pedestal_upper_nut_z'][1]-S['fasteners']['M3']['nut_height_max'])).val()
        items[f'HW_M3x20_pedestal_bottom_{i}']=place(bolt(3,20),(x,y,0),(1,0,0),(0,0,-1))
        items[f'HW_M3nut_pedestal_bottom_{i}']=nut(3).translate((x,y,B['pedestal_lower_nut_z'][0])).val()
    for i,x in enumerate(B['knockover_mount_holes_x']):
        items[f'B07_knockover_post_{i}']=ps['B07_knockover_post'].translate((x,0,0)).val()
        for j,z in enumerate(B['knockover_mount_holes_z']):
            items[f'HW_M3x16_knockover_{i}_{j}']=place(bolt(3,16),(x,B['knockover_y'],z),(1,0,0),(0,-1,0))
            items[f'HW_M3nut_knockover_{i}_{j}']=place(nut(3),(x,B['post_nut_y'][0],z),(1,0,0),(0,1,0))
        for j,dx in enumerate((-12.0,12.0)):
            y=B['knockover_post_front_y']+B['knockover_post_depth']/2;under=F['base_size'][2]+B['post_foot_height']
            items[f'HW_M3x25_post_{i}_{j}']=bolt(3,25).translate((x+dx,y,under)).val()
            items[f'HW_M3nut_post_{i}_{j}']=nut(3).translate((x+dx,y,-S['fasteners']['M3']['nut_height_max'])).val()
    for i,(x,y) in enumerate(F['foot_centers']):
        items[f'F04_foot_{i}']=ps['F04_foot'].translate((x,y,0)).val()
        under=F['base_size'][2]-F['foot_counterbore_depth']
        items[f'HW_M3x16_foot_{i}']=bolt(3,16).translate((x,y,under)).val()
        items[f'HW_M3nut_foot_{i}']=nut(3).translate((x,y,F['foot_nut_roof_z']-S['fasteners']['M3']['nut_height_max'])).val()
    return items

def parts():
    result={'H01_hook_body':hook_body(),'H02_gate':gate(),'H03_barrel_stop':barrel(), 'H04_bearing':bearing(),
            'H05_rear_collar':collar(T['bearing_back']-T['collar_axial_gap']-T['collar_thickness']),
            'H06_front_collar':collar(T['bearing_front']+T['collar_axial_gap']),
            'H07_gate_knob':gate_knob(),'H08_stop_sleeve':stop_sleeve(),
            'G01_guide_tube':guide_tube(),'G02_guide_mount':guide_mount(),'A02_carriage':slide_carriage()}
    result.update(B01_bed=support_bed(),B02_cover=support_cap(),B03_carriage=support_carriage(),B04_pair_holder=support_holder(),B05_pair_knob=pair_knob(),B06_knockover=knockover(),F01_z_bracket=z_bracket(),F02_head_adapter=head_adapter())
    result.update(B07_knockover_post=knockover_post(),B08_pedestal=bed_pedestal(),F03_base_board=base_board(),F04_foot=base_foot())
    result.update(G07_exit_reducer=guide_reducer(),G06_exit_insert=guide_insert(),G03_outer_tube=guide_outer(),G04_front_bush=guide_bush(),G05_rear_bush=guide_bush(True),F05_guide_adapter=guide_adapter(),F06_guide_z_bracket=z_bracket(True))
    for name,L in sorted(P['lengths'].items()):
        if name=='y': continue # same manufactured 160mm part as x
        result[f'A01_{name}_rail']=slide_base(L) if name not in ('z','gz') else slide_base(L).mirror('XZ')
        result[f'A03_{name}_cap_L']=slide_cap(L,-1)
        result[f'A04_{name}_cap_R']=slide_cap(L,1)
        result[f'A05_{name}_stop_L']=slide_stop(L,-1)
        result[f'A06_{name}_stop_R']=slide_stop(L,1)
    result.update(peripherals.parts(sys.modules[__name__]))
    return result

def place(obj, origin, xdir, normal):
    return obj.val().moved(cq.Location(cq.Plane(origin=origin,xDir=xdir,normal=normal)))

def bank_instances(ps, support_q=None, gate_q=None):
    B=S['support_bank']; support_q=support_q or [0.0]*B['station_count']; gate_q=gate_q or [0.0]*B['station_count']
    items={k:ps[k].val() for k in ('B01_bed','B02_cover','B06_knockover')}
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']; q=support_q[i]; origin=(x,B['standard_tip_y']+T['body_tip']+q,B['tool_axis_z'])
        items[f'B03_carriage_{i}']=place(ps['B03_carriage'],(x,B['bank_origin'][1]+q,B['bank_origin'][2]),(0,1,0),(0,0,1))
        items[f'B04_holder_{i}']=place(ps['B04_pair_holder'],origin,(0,-1,0),(-1,0,0))
        items[f'B05_knob_{i}']=place(ps['B05_pair_knob'].translate((-gate_q[i],0,0)),origin,(0,-1,0),(-1,0,0))
        for j,off in enumerate((-B['pair_centers']/2,B['pair_centers']/2)):
            items[f'H01_support_{i}_{j}']=place(ps['H01_hook_body'].translate((0,0,off)),origin,(0,-1,0),(-1,0,0))
            items[f'H02_support_gate_{i}_{j}']=place(ps['H02_gate'].translate((-gate_q[i],0,off)),origin,(0,-1,0),(-1,0,0))
            items[f'H08_support_sleeve_{i}_{j}']=place(ps['H08_stop_sleeve'].translate((-gate_q[i],0,off)),origin,(0,-1,0),(-1,0,0))
    return items

def hook_instances(ps, gate_q=0.0):
    result={}
    for name,obj in ps.items():
        if not name.startswith('H'): continue
        if name in ('H02_gate','H07_gate_knob','H08_stop_sleeve'): obj=obj.translate((-gate_q,0,0))
        result[name]=obj.val()
    return result

def slide_instances(ps, q=0.0, kind='x'):
    result={}
    for name in (f'A01_{kind}_rail','A02_carriage',f'A03_{kind}_cap_L',f'A04_{kind}_cap_R',f'A05_{kind}_stop_L',f'A06_{kind}_stop_R'):
        obj=ps[name]
        if name=='A02_carriage': obj=obj.translate((q,0,0))
        result[name]=obj.val()
    return result

def export_assembly(items,name):
    a=cq.Assembly(name=name)
    for key,solid in items.items(): a.add(solid,name=key)
    a.save(str(OUT/f'{name}.step'))
    return {key:{'bbox_mm':[solid.BoundingBox().xmin,solid.BoundingBox().xmax,solid.BoundingBox().ymin,solid.BoundingBox().ymax,solid.BoundingBox().zmin,solid.BoundingBox().zmax],'volume_mm3':solid.Volume()} for key,solid in items.items()}

@lru_cache(maxsize=None)
def bolt(d,L):
    f=S['fasteners'][f'M{d}']
    # Major-diameter shank/head envelopes; helical threads are deliberately absent.
    return cyl_z(-L,0,d/2).union(cyl_z(0,f['head_height_max'],f['head_d_max']/2))

@lru_cache(maxsize=None)
def nut(d):
    f=S['fasteners'][f'M{d}']
    return hex_z(0,f['nut_height_max'],f['nut_af_max']).cut(cyl_z(-1,f['nut_height_max']+1,d/2))

def add_hook_hardware(items):
    for i,u in enumerate(T['body_fix_holes_u']):
        z=T['barrel_d']/2-T['barrel_bolt_counterbore_depth']
        items[f'HW_M2x12_body_{i}']=bolt(2,T['body_bolt_length']).translate((u,T['body_fix_hole_v'],z)).val()
        items[f'HW_M2nut_body_{i}']=nut(2).translate((u,T['body_fix_hole_v'],-T['barrel_d']/2+T['barrel_nut_depth']-S['fasteners']['M2']['nut_height_max'])).val()
    for i,a in enumerate((T['bearing_back']-T['collar_axial_gap']-T['collar_thickness'],T['bearing_front']+T['collar_axial_gap'])):
        u=a+T['collar_thickness']/2
        items[f'HW_M3x20_collar_{i}']=bolt(3,T['collar_bolt_length']).translate((u,12,T['collar_ear_half_width'])).val()
        items[f'HW_M3nut_collar_{i}']=nut(3).translate((u,12,-T['collar_ear_half_width']-S['fasteners']['M3']['nut_height_max'])).val()
    v=T['gate_stop_plate_offset_v']+T['gate_stop_plate_thickness']+T['stop_axial_clearance']
    origin=(T['gate_tail_hole_u'],v,0)
    items['HW_M2x20_gate']=place(bolt(2,T['gate_stop_bolt_length']),origin,(1,0,0),(0,1,0))
    vnut=T['gate_bottom']-T['gate_knob_height']+T['gate_knob_nut_pocket_depth']-S['fasteners']['M2']['nut_height_max']
    items['HW_M2nut_gate']=place(nut(2),(T['gate_tail_hole_u'],vnut,0),(1,0,0),(0,1,0))
    u=(T['bearing_back']+T['bearing_front'])/2
    items['HW_M3x12_roll_lock']=place(bolt(3,12),(u,T['barrel_d']/2+12+T['roll_lock_clearance'],0),(1,0,0),(0,1,0))
    items['HW_M3nut_roll_lock']=place(nut(3),(u,T['roll_lock_nut_v'][0],0),(1,0,0),(0,1,0))
    return items

def add_bank_hardware(items,support_q=None,gate_q=None):
    B=S['support_bank']; oz=B['bank_origin'][2]
    support_q=support_q or [0.0]*B['station_count']; gate_q=gate_q or [0.0]*B['station_count']
    for i in range(B['station_count']):
        x=B['first_station_x']+i*B['station_pitch']; origin=(x,B['standard_tip_y']+T['body_tip']+support_q[i],B['tool_axis_z'])
        # M2 x20 retained within each lane, rather than projecting into its neighbor.
        for k,u in enumerate(t for t in T['body_fix_holes_u'] if B['clamp_back_u']<t<B['clamp_front_u']):
            local=bolt(2,20).translate((u,T['body_fix_hole_v'],B['clamp_width']/2))
            items[f'HW_M2x20_support_{i}_{k}']=place(local,origin,(0,-1,0),(-1,0,0))
            local=nut(2).translate((u,T['body_fix_hole_v'],-B['clamp_width']/2+T['barrel_nut_depth']-S['fasteners']['M2']['nut_height_max']))
            items[f'HW_M2nut_support_{i}_{k}']=place(local,origin,(0,-1,0),(-1,0,0))
        for j,off in enumerate((-B['pair_centers']/2,B['pair_centers']/2)):
            v=T['gate_stop_plate_offset_v']+T['gate_stop_plate_thickness']+T['stop_axial_clearance']
            local=cq.Workplane().newObject([place(bolt(2,T['gate_stop_bolt_length']),(T['gate_tail_hole_u']-gate_q[i],v,off),(1,0,0),(0,1,0))])
            items[f'HW_M2x20_gate_{i}_{j}']=place(local,origin,(0,-1,0),(-1,0,0))
            vn=T['gate_bottom']-T['gate_knob_height']+T['gate_knob_nut_pocket_depth']-S['fasteners']['M2']['nut_height_max']
            local=cq.Workplane().newObject([place(nut(2),(T['gate_tail_hole_u']-gate_q[i],vn,off),(1,0,0),(0,1,0))])
            items[f'HW_M2nut_gate_{i}_{j}']=place(local,origin,(0,-1,0),(-1,0,0))
        py=B['bank_origin'][1]+B['index_arm_u']+support_q[i]; pz=oz+B['bank_carriage_top']+B['index_arm_height']
        if support_q[i] in B['index_offsets_y']: items[f'HW_M3x30_index_{i}']=bolt(3,B['index_pin_length']).translate((x,py,pz)).val()
        # Upward mounting screws seat inside the carriage's bottom-access pockets.
        for j,du in enumerate((-P['mount_hole_pitch']/2,P['mount_hole_pitch']/2)):
            py=B['bank_origin'][1]+du+support_q[i]; under=oz+B['bank_carriage_top']-5.5
            items[f'HW_M3x12_holder_{i}_{j}']=place(bolt(3,12),(x,py,under),(1,0,0),(0,0,-1))
            nz=B['tool_axis_z']+B['holder_nut_floor_v']
            items[f'HW_M3nut_holder_{i}_{j}']=nut(3).rotate((0,0,0),(0,0,1),90).translate((x,py,nz)).val()
    for i,x in enumerate(B['bank_cap_bolt_x']):
        for j,y in enumerate(B['bank_cap_bolt_y']):
            z=oz+B['bank_top']+B['bank_cap_thickness']
            items[f'HW_M2x16_cover_{i}_{j}']=bolt(2,16).translate((x,y,z)).val()
            items[f'HW_M2nut_cover_{i}_{j}']=nut(2).translate((x,y,oz+4.4-S['fasteners']['M2']['nut_height_max'])).val()
    return items

def transformed(items,origin,xdir,normal,prefix=''):
    loc=cq.Location(cq.Plane(origin=origin,xDir=xdir,normal=normal))
    return {prefix+k:v.moved(loc) for k,v in items.items()}

@lru_cache(maxsize=None)
def slide_cap_bolt():
    return cyl_z(-12,0,1.5).union(cyl_z(0,P["cap_head_height"],P["cap_head_d"]/2))

def add_slide_hardware(items,q,kind):
    L=P['lengths'][kind]; f=S['fasteners']['M3']; sign=-1 if kind in ('z','gz') else 1
    for i,x in enumerate((-L/2+P['cap_bolt_end_inset'],L/2-P['cap_bolt_end_inset'])):
        for j,y in enumerate((-P['cap_bolt_y'],P['cap_bolt_y'])):
            z=P['wall_top']+P['cap_thickness']-P['cap_counterbore_depth']
            capbolt=slide_cap_bolt()
            items[f'HW_buttonM3x12_cap_{i}_{j}']=capbolt.translate((x,y,z)).val()
            items[f'HW_M3nut_cap_{i}_{j}']=nut(3).translate((x,y,P['cap_nut_pocket_roof']-f['nut_height_max'])).val()
    for i,sgn in enumerate((-1,1)):
        x=sgn*(L/2-P['endstop_thickness']/2)
        for j,y in enumerate((-P['endstop_hole_y'],P['endstop_hole_y'])):
            z=P['endstop_top']-P['counterbore_depth']
            items[f'HW_M3x12_stop_{i}_{j}']=bolt(3,12).translate((x,y,z)).val()
            items[f'HW_M3nut_stop_{i}_{j}']=nut(3).translate((x,y,P['endstop_nut_roof']-f['nut_height_max'])).val()
    z=P['floor_thickness']+P['carriage_flange_height']/2
    items['HW_M3x12_slide_lock']=place(bolt(3,12),(0,sign*(P['carriage_width']/2+12+0.2),z),(1,0,0),(0,sign,0))
    items['HW_M3nut_slide_lock']=place(nut(3),(0,sign*P['lock_nut_inner_y'],z),(1,0,0),(0,sign,0))
    for j,x in enumerate((-8,8)):
        items[f'HW_M3nut_carriage_{j}']=nut(3).translate((x+q,0,P['nut_pocket_roof']-f['nut_height_max'])).val()
    return items

def xyz_instances(ps,origin,q,guide=False):
    ox,oy,oz=origin; qx,qy,qz=q; xc=ox+qx; yc=oy+qy
    zrel=36+(S['frame']['guide_z_axis_center_above_xy'] if guide else S['frame']['z_axis_center_above_xy'])
    items={}
    xslide=add_slide_hardware(slide_instances(ps,qx,'x'),qx,'x')
    items.update(transformed(xslide,(ox,oy,oz),(1,0,0),(0,0,1),'X_'))
    kind='gy' if guide else S['frame']['head_y_rail_kind']
    yslide=add_slide_hardware(slide_instances(ps,qy,kind),qy,kind)
    items.update(transformed(yslide,(xc,oy,oz+18),(0,1,0),(0,0,1),'Y_'))
    bracket='F06_guide_z_bracket' if guide else 'F01_z_bracket'
    items[bracket]=ps[bracket].translate((xc,yc,oz+36)).val()
    zkind='gz' if guide else 'z'
    zslide=add_slide_hardware(slide_instances(ps,qz,zkind),qz,zkind)
    items.update(transformed(zslide,(xc,yc-14,oz+zrel),(0,0,1),(0,1,0),'Z_'))
    for j,a in enumerate((-8,8)):
        items[f'HW_M3x20_base_{j}']=bolt(3,20).translate((ox+a,oy,oz+2.8)).val()
        items[f'HW_M3nut_base_{j}']=nut(3).translate((ox+a,oy,-2.4)).val()
        items[f'HW_M3x12_XY_{j}']=bolt(3,12).translate((xc+a,oy,oz+20.8)).val()
        items[f'HW_M3x12_bracket_{j}']=bolt(3,12).translate((xc,yc+a,oz+38.8)).val()
        items[f'HW_M3x12_Zbase_{j}']=place(bolt(3,12),(xc,yc-11.2,oz+zrel+a),(0,0,1),(0,1,0))
        items[f'HW_M3nut_Zbase_{j}']=place(nut(3),(xc,yc-22.4,oz+zrel+a),(0,0,1),(0,1,0))
    if guide:
        items={k:v.rotate((ox,oy,0),(ox,oy,1),180) for k,v in items.items()}
    return items

def joint_coordinates(head_tip,guide_tip):
    F=S['frame']; hx,hy,hz=head_tip; gx,gy,gz=guide_tip
    th=math.radians(T['inclination_deg']); co=math.cos(th); si=math.sin(th); gc,gs,_,_=guide_frame()
    return {'head':(hx-(F['head_x_origin'][0]+F['tool_lateral_offset']),hy-(F['head_x_origin'][1]+12+41*co+26*si),hz-(F['head_x_origin'][2]+36+F['z_axis_center_above_xy']-41*si+26*co)),
            'guide':(F['guide_x_origin'][0]-F['guide_lateral_offset']-gx,F['guide_x_origin'][1]-172*gc-gy,gz+145*gs-(F['guide_x_origin'][2]+36+F['guide_z_axis_center_above_xy']))}

def joint_limit_violations(head_tip,guide_tip):
    F=S['frame']; q=joint_coordinates(head_tip,guide_tip); result=[]
    for group,kinds in (('head',('x',F['head_y_rail_kind'],'z')),('guide',('x','gy','gz'))):
        for axis,kind,value in zip('xyz',kinds,q[group]):
            limit=(P['lengths'][kind]-2*P['endstop_thickness']-P['carriage_length'])/2
            if abs(value)>limit+1e-8:result.append({'axis':group+'_'+axis,'q_mm':value,'limit_mm':limit})
    return result

def integrated_instances(ps,head_tip=None,guide_tip=None,head_gate=0,carrier_z=160,takedown_z=50,feed_mode="high",head_roll=0,support_q=None,support_gate_q=None):
    F=S['frame']; A=S['assembly']; G=S['guide']
    hx,hy,hz=head_tip or A['head_reference_tip']; gx,gy,gz=guide_tip or A['guide_reference_tip']
    th=math.radians(T['inclination_deg']); c=math.cos(th); sn=math.sin(th)
    # Mount-derived rigid transforms. See DIMENSIONS_AND_INTERFACES for the inverse map.
    hq=joint_coordinates((hx,hy,hz),(gx,gy,gz))['head']
    gc,gs,geu,gew=guide_frame()
    gzc=gz+145*gs
    gq=joint_coordinates((hx,hy,hz),(gx,gy,gz))['guide']
    result=add_bank_mounts(add_bank_hardware(bank_instances(ps,support_q,support_gate_q),support_q,support_gate_q),ps)
    result.update({'HEAD_'+k:v for k,v in xyz_instances(ps,F['head_x_origin'],hq).items()})
    result.update({'GUIDE_'+k:v for k,v in xyz_instances(ps,F['guide_x_origin'],gq,True).items()})
    origin=(hx,hy-5*c,hz+5*sn)
    local=add_hook_hardware(hook_instances(ps,head_gate))
    # Hardware attached to the translated gate must follow the same actuator.
    for k in ('HW_M2x20_gate','HW_M2nut_gate'):
        local[k]=local[k].translate((-head_gate,0,0))
    local['F02_head_adapter']=ps['F02_head_adapter'].val()
    for j,u in enumerate((-44,-28)):
        local[f'HW_M3x25_bearing_{j}']=place(bolt(3,25),(u,-34,0),(1,0,0),(0,-1,0))
        local[f'HW_M3nut_bearing_{j}']=place(nut(3),(u,-13.4,0),(1,0,0),(0,1,0))
    fixed={'H04_bearing','F02_head_adapter','HW_M3x12_roll_lock','HW_M3nut_roll_lock'}
    for k in local:
        if k not in fixed and 'bearing_' not in k:
            local[k]=local[k].rotate((0,0,0),(1,0,0),head_roll)
    result.update(transformed(local,origin,(0,c,-sn),(1,0,0),'TOOL_'))
    xc=F['head_x_origin'][0]+hq[0];yc=F['head_x_origin'][1]+hq[1];zc=F['head_x_origin'][2]+36+F['z_axis_center_above_xy']+hq[2]
    for j,z in enumerate((-8,8)):
        result[f'HEAD_HW_M3x12_adapter_{j}']=place(bolt(3,12),(xc,yc+7.5,zc+z),(0,0,1),(0,1,0))
    gxc=F['guide_x_origin'][0]-gq[0];gyc=F['guide_x_origin'][1]-gq[1]
    result['GUIDE_F05_adapter']=ps['F05_guide_adapter'].translate((gxc,gyc,gzc)).val()
    for j,z in enumerate((-8,8)):
        result[f'GUIDE_HW_M3x12_adapter_{j}']=place(bolt(3,12),(gxc,gyc-7.5,gzc+z),(0,0,1),(0,-1,0))
    local={k:ps[k].val() for k in ('G01_guide_tube','G02_guide_mount','G03_outer_tube','G04_front_bush','G05_rear_bush','G06_exit_insert','G07_exit_reducer')}
    u=G['mount_back_u']+G['mount_block'][0]/2
    local['HW_M3x12_outer_lock']=place(bolt(3,12),(u,G['outer_tube_od']/2+12+0.2,0),(1,0,0),(0,1,0))
    local['HW_M3nut_outer_lock']=place(nut(3),(u,G['outer_lock_nut_v'][0],0),(1,0,0),(0,1,0))
    for j,u in enumerate((-153,-137)):
        local[f'HW_M3x25_holder_{j}']=bolt(3,25).translate((u,G['mount_hole_offset_v'],8)).val()
        local[f'HW_M3nut_holder_{j}']=nut(3).translate((u,G['mount_hole_offset_v'],-14.4)).val()
    result.update(transformed(local,(gx,gy,gz),geu,gew,'GUIDE_TOOL_'))
    return peripherals.add(result,ps,sys.modules[__name__],carrier_z,takedown_z,feed_mode)

def build():
    OUT.mkdir(exist_ok=True,parents=True); ps=parts(); manifest={}
    for name,obj in ps.items():
        solid=obj.val(); bb=solid.BoundingBox()
        if not solid.isValid() or len(obj.solids().vals())!=1: raise ValueError(f'{name}: invalid or disconnected')
        cq.exporters.export(obj,str(OUT/f'{name}.step'))
        cq.exporters.export(obj,str(OUT/f'{name}.stl'),tolerance=0.03,angularTolerance=0.1)
        manifest[name]={'solids':len(obj.solids().vals()),'valid':solid.isValid(),'volume_mm3':solid.Volume(),
                        'bbox_mm':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax]}
    for name in ('H01_hook_body','H02_gate'):
        # Drawing plane explicitly documented; output has true arcs, not a rendered image.
        obj=ps[name] if name=='H01_hook_body' else ps[name].rotate((0,0,0),(1,0,0),90).translate((0,0,-T['gate_bottom']-T['gate_thickness']/2))
        cq.exporters.export(obj.section(),str(OUT/f'{name}_profile.dxf'))
    assembly=cq.Assembly(name='R5M2_experimental_hook_tool')
    for name,obj in ps.items():
        if name.startswith('H'): assembly.add(obj,name=name)
    assembly.save(str(OUT/'hook_tool.step'))
    guide=cq.Assembly(name='R5M2_experimental_guide')
    for name in ('G01_guide_tube','G02_guide_mount','G03_outer_tube','G04_front_bush','G05_rear_bush','G06_exit_insert','G07_exit_reducer'): guide.add(ps[name],name=name)
    guide.save(str(OUT/'guide_tool.step'))
    slide=cq.Assembly(name='R5M2_manual_slide_160')
    for name in ('A01_x_rail','A02_carriage','A03_x_cap_L','A04_x_cap_R','A05_x_stop_L','A06_x_stop_R'):
        slide.add(ps[name],name=name)
    slide.save(str(OUT/'manual_slide_160.step'))
    export_assembly(add_hook_hardware(hook_instances(ps)),'hook_tool_with_hardware')
    mounted_manifest=export_assembly(add_bank_mounts(add_bank_hardware(bank_instances(ps)),ps),'mounted_support_testbed')
    (OUT/'mounted_support_instances.json').write_text(json.dumps(mounted_manifest,indent=2)+'\n')
    export_assembly(bank_instances(ps),'support_bank')
    bank_manifest=export_assembly(add_bank_hardware(bank_instances(ps)),'support_bank_with_hardware')
    (OUT/'support_bank_instances.json').write_text(json.dumps(bank_manifest,indent=2)+'\n')
    full=integrated_instances(ps)
    full_manifest=export_assembly(full,'integrated_rigid_fixture')
    (OUT/'integrated_instances.json').write_text(json.dumps(full_manifest,indent=2)+'\n')
    metadata={'revision':S['revision'],'spec_sha256':hashlib.sha256(SPEC.read_bytes()).hexdigest(),
              'cadquery':cq.__version__,'scope':'Parametric crochet research fixture assembly',
              'status':'Research prototype','parts':manifest}
    (OUT/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({'parts':len(ps),'valid':True,'output':str(OUT),'scope':metadata['scope']}))

if __name__=='__main__': build()
