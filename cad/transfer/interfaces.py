"""Explicit local head hardware, manual lift stop and rod/pin retention."""
import json

def add_interfaces(base,C,parts):
    cq=base.cq;T=base.T;I=json.loads((base.ROOT/'spec/transfer_interfaces.json').read_text())
    gap=(T['stop_sleeve_od']+T['stop_slot_side_clearance']-T['stop_sleeve_od'])/2
    barrel=base.barrel(gate_travel=C['gate_open_mm'],stop_plate_back=I['gate_stop_back_u_mm'])
    head={'H03_barrel_stop':barrel,'H04_bearing':base.bearing(),'H05_rear_collar':base.collar(T['bearing_back']-T['collar_axial_gap']-T['collar_thickness']),'H06_front_collar':base.collar(T['bearing_front']+T['collar_axial_gap']),'H07_gate_knob':base.gate_knob(),'H08_stop_sleeve':base.stop_sleeve()}
    hardware=base.add_hook_hardware({})
    for n,p in head.items():
        if n=='H04_bearing':p=p.rotate((0,0,0),(1,0,0),-20.)
        parts['TH_'+n]=p
    for n,p in hardware.items():
        if 'roll_lock' in n:p=p.rotate((0,0,0),(1,0,0),-20.)
        parts['TH_'+n]=cq.Workplane(obj=p)
    a=C['stripper_channel_mm']/2+C['stripper_plate_thickness_mm']+C['lift_carriage_plate_gap_mm'];b=a+C['lift_pin_embed_mm'];park=C['lift_park_v_mm']
    carriage=parts['R05_lift_carriage'];anchor=parts['R06_anchor'];eu0,eu1=I['lift_ear_u_mm'];ev0,ev1=I['lift_ear_v_mm'];ew=I['lift_ear_half_w_mm'];fu0,fu1=I['fork_u_mm'];fv0,fv1=I['fork_v_mm'];wi=I['fork_wing_inner_w_mm'];wout=I.get('fork_wing_outer_w_mm',C['lift_guide_w_mm']+3)
    carriage=carriage.union(base.box(b,eu1,park+C['lift_carriage_top_offsets_mm'][0],park+C['lift_carriage_top_offsets_mm'][1],-ew,ew)).union(base.box(eu0,eu1,ev0,ev1,-ew,ew))
    v=I['lift_stop_center_v_mm'];rad=(T['stop_sleeve_od']+T['stop_slot_side_clearance'])/2;stroke=C['lift_high_v_mm']-park
    lo=v-stroke+gap;hi=v-gap
    slot=base.box(eu0-1,eu1+1,lo,hi,-rad,rad)
    for h in [lo,hi]:slot=slot.union(base.cyl_x(eu0-1,eu1+1,rad,h,0))
    carriage=carriage.cut(slot)
    back=C['stripper_channel_mm']/2+C['stripper_plate_thickness_mm']+C['anchor_depth_mm']
    if 'anchor_crossbar_u_mm' in I:
        ca,cb=I['anchor_crossbar_u_mm'];anchor=anchor.union(base.box(ca,cb,*I.get('anchor_crossbar_v_mm',C['anchor_v_bounds_mm']),-wout,wout))
        if 'anchor_crossbar_v_mm' not in I:
            for w in [-C['anchor_bolt_w_mm'],C['anchor_bolt_w_mm']]:anchor=anchor.cut(base.cyl_x(ca,cb+1,2.94,C['anchor_bolt_v_mm'],w))
    for sign in [-1,1]:
        w0,w1=sorted([sign*wi,sign*wout]);anchor=anchor.union(base.box(back,fu1,fv0,fv1,w0,w1))
    anchor=anchor.union(base.box(fu0,fu1,fv0,fv1,-wout,wout))
    for w in I['frame_port_w_mm']:anchor=anchor.cut(base.cyl_x(fu0-1,fu1+1,I['frame_port_d_mm']/2,I['frame_port_v_mm'],w))
    sa,sb=I['lift_stop_sleeve_u_mm']
    anchor=anchor.cut(base.cyl_x(fu0-1,fu1+1,I['clamp_screw_clearance_mm']/2,v,0)).cut(base.cyl_x(fu0-1,sb,I['lift_stop_pilot_d_mm']/2,v,0))
    parts['R11_lift_stop_sleeve']=base.cyl_x(sa,sb,T['stop_sleeve_od']/2,v,0).cut(base.cyl_x(sa-1,sb+1,T['stop_sleeve_id']/2,v,0))
    parts['R12_lift_stop_screw']=cq.Workplane(obj=base.place(base.bolt(2,I['lift_stop_screw_length_mm']),(fu1,v,0),(0,0,1),(1,0,0)))
    parts['R13_lift_stop_nut']=cq.Workplane(obj=base.place(base.nut(2),(sa,v,0),(0,0,1),(-1,0,0)))
    # Side-access trapped nuts and flat-ended radial clamp screws.
    wout=C['lift_guide_w_mm']+3
    rod_u=(a+b)/2+C['lift_guide_u_offset_mm'];vv=I['guide_screw_v_mm'];seat=I['guide_screw_seat_w_mm'];nh=base.S['fasteners']['M2']['nut_height_max'];af=I['clamp_nut_pocket_af_mm'];clear=I['clamp_screw_clearance_mm']/2
    pocket_height=I['clamp_nut_pocket_height_mm']
    for idx,sign in enumerate([-1,1]):
        w0,w1=sorted([sign*wout,sign*seat]);anchor=anchor.union(base.box(rod_u-2.5,rod_u+2.5,vv-2.5,vv+2.5,w0,w1))
        w0,w1=sorted([sign*(C['lift_guide_w_mm']+C['lift_guide_radius_mm']-.1),sign*(seat+1)])
        anchor=anchor.cut(base.cyl_z(w0,w1,clear,rod_u,vv))
        w0,w1=sorted([sign*(wout+nh-pocket_height),sign*(wout+nh)])
        anchor=anchor.cut(base.hex_z(w0,w1,af,rod_u,vv)).cut(base.box(rod_u+1.5,back+1,vv-af/2,vv+af/2,w0,w1))
        parts[f'R14_rod_clamp_screw_{idx}']=cq.Workplane(obj=base.place(base.bolt(2,I['guide_clamp_screw_length_mm']),(rod_u,vv,sign*seat),(1,0,0),(0,0,sign)))
        parts[f'R15_rod_clamp_nut_{idx}']=cq.Workplane(obj=base.place(base.nut(2),(rod_u,vv,sign*wout),(1,0,0),(0,0,sign)))
    if C.get('pin_shuttle',False):
        su0,su1=I['pin_shuttle_u_mm'];sv0,sv1=I['pin_shuttle_v_mm'];sw=I['pin_shuttle_half_w_mm'];pu=(su0+su1)/2
        shuttle=base.box(su0,su1,sv0,sv1,-sw,sw)
        for idx,sign in enumerate([-1,1]):
            w=sign*C['lift_pin_w_mm'];shuttle=shuttle.cut(base.cyl_x(su0-1,su1+1,C['lift_pin_running_bore_d_mm']/2,park,w))
            shuttle=shuttle.cut(base.cyl_y(park,sv1+1,clear,pu,w)).cut(base.hex_y(nh-pocket_height,nh,af,pu,w)).cut(base.box(pu+1.5,su1+1,nh-pocket_height,nh,w-af/2,w+af/2))
            parts[f'R16_pin_clamp_screw_{idx}']=cq.Workplane(obj=base.place(base.bolt(2,4),(pu,sv1,w),(1,0,0),(0,1,0)))
            parts[f'R17_pin_clamp_nut_{idx}']=cq.Workplane(obj=base.place(base.nut(2),(pu,0,w),(1,0,0),(0,1,0)))
            parts[f'R03_lift_pin_{idx}']=base.cyl_x(-C['stripper_channel_mm']/2-C['stripper_plate_thickness_mm']-C['lift_pin_protrusion_mm'],I['pin_end_u_mm'],C['lift_pin_radius_mm'],park,w)
        bu0,bu1=I['reset_bridge_u_mm'];bv0,bv1=I['reset_bridge_v_mm'];v=I['reset_stop_axis_v_mm']
        carriage=carriage.union(base.box(bu0,bu1,bv0,bv1,-sw,sw))
        for w in [-C['lift_pin_w_mm'],C['lift_pin_w_mm']]:carriage=carriage.union(base.box(bu0,bu1,bv0,park+C['lift_carriage_top_offsets_mm'][0],w-C['lift_carriage_column_width_mm']/2,w+C['lift_carriage_column_width_mm']/2))
        for w in [-C['lift_pin_w_mm'],C['lift_pin_w_mm']]:carriage=carriage.cut(base.cyl_x(bu0-1,bu1+1,C['lift_pin_running_bore_d_mm']/2,park,w))
        carriage=carriage.cut(base.cyl_x(bu0-1,bu1+1,clear,v,0))
        face=I['reset_nut_face_u_mm']
        pocket=base.hex_z(0,pocket_height,af)
        carriage=carriage.cut(cq.Workplane(obj=base.place(pocket,(face,v,0),(0,0,1),(-1,0,0))))
        # Side opening exposes the captured nut; hardware is inserted before the sleeve.
        carriage=carriage.cut(base.box(face-pocket_height,face,v-af/2,v+af/2,0,sw+1))
        sa,sb=I['reset_sleeve_u_mm'];od=T['stop_sleeve_od'];id_=T['stop_sleeve_id']
        parts['R20_reset_sleeve']=base.cyl_x(sa,sb,od/2,v).cut(base.cyl_x(sa-1,sb+1,id_/2,v))
        for name,limits,hole in [('R21_reset_front_washer',I['reset_washer_front_u_mm'],I['reset_front_washer_bore_d_mm']),('R22_reset_rear_washer',I['reset_washer_rear_u_mm'],2.2)]:
            parts[name]=base.cyl_x(*limits,3.,v).cut(base.cyl_x(limits[0]-1,limits[1]+1,hole/2,v))
        parts['R23_reset_screw']=cq.Workplane(obj=base.place(base.bolt(2,I['reset_stop_screw_length_mm']),(I['reset_stop_screw_seat_u_mm'],v,0),(0,0,1),(1,0,0)))
        parts['R24_reset_nut']=cq.Workplane(obj=base.place(base.nut(2),(face,v,0),(0,0,1),(-1,0,0)))
        shuttle=shuttle.cut(base.cyl_x(su0-1,su1+1,(od+.2)/2,v,0));parts['R19_pin_shuttle']=shuttle
    else:
        bh=I['pin_clamp_boss_halfwidth_mm'];pu=b-bh;seat=I['pin_screw_seat_w_mm'];nw0,nw1=I['pin_nut_w_mm']
        for idx,sign in enumerate([-1,1]):
            w=sign*C['lift_pin_w_mm'];w0,w1=sorted([sign*(C['lift_pin_w_mm']+C['lift_pin_radius_mm']),sign*seat])
            carriage=carriage.union(base.box(pu-bh,pu+bh,park-bh,park+bh,w0,w1))
            w0,w1=sorted([sign*C['lift_pin_w_mm'],sign*(seat+1)])
            carriage=carriage.cut(base.cyl_z(w0,w1,clear,pu,park))
            w0,w1=sorted([sign*min(nw0,nw1-pocket_height),sign*nw1])
            carriage=carriage.cut(base.hex_z(w0,w1,af,pu,park)).cut(base.box(pu+1.5,b+1,park-af/2,park+af/2,w0,w1))
            carriage=carriage.cut(base.cyl_x(a-1,b+1,C['lift_pin_running_bore_d_mm']/2,park,w))
            parts[f'R16_pin_clamp_screw_{idx}']=cq.Workplane(obj=base.place(base.bolt(2,I['pin_clamp_screw_length_mm']),(pu,park,sign*seat),(1,0,0),(0,0,sign)))
            parts[f'R17_pin_clamp_nut_{idx}']=cq.Workplane(obj=base.place(base.nut(2),(pu,park,sign*nw0),(1,0,0),(0,0,sign)))
    parts['R05_lift_carriage']=carriage;parts['R06_anchor']=anchor
    return parts

def motion_kind(name):
    if name in ['H01_hook_body']:return 'head'
    if name=='H02_gate':return 'gate'
    if name.startswith('TH_'):
        return 'gate' if any(x in name for x in ['H07_gate','H08_stop','HW_M2x20_gate','HW_M2nut_gate']) else 'head'
    if name=='R05_lift_carriage' or name.startswith(('R03_lift_pin','R16_pin','R17_pin','R19_','R20_','R21_','R22_','R23_','R24_')):return 'lift'
    return 'fixed'


def resets_with_shuttle(name):
    return name.startswith(('R03_lift_pin','R16_pin','R17_pin','R19_pin_shuttle'))

def motion_shift(name,advance,gate,lift,reset=0.):
    shift={'head':[advance,0.,0.],'gate':[advance-gate,0.,0.],'lift':[0.,lift,0.],'fixed':[0.,0.,0.]}[motion_kind(name)]
    if resets_with_shuttle(name):shift[0]+=reset
    return tuple(shift)
