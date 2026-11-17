"""Physical X_T index/park carriage and manually rekeyed transfer shoe.

No solver or export on import. Existing single-station installation is unchanged;
`installed` is the explicit integration API for this adopted candidate.
"""
import json
import math
from functools import lru_cache
import numpy as np
from cad.r5m2 import build as base
from cad.transfer import installation as original
from cad.transfer.interfaces import motion_shift

SPEC=base.ROOT/'spec/indexed_transfer.json'
S=json.loads(SPEC.read_text())
cq=base.cq


@lru_cache(maxsize=1)
def transfer_parts():
    from cad.transfer.build import parts as make_parts
    return make_parts()


def transform(shape,x,roll=0):
    _,u,origin=original.reference_frame();origin=origin.copy();origin[0]=x
    return base.transformed({'p':shape.rotate((0,0,0),(1,0,0),roll)},tuple(origin),tuple(u),(1,0,0))['p']


def detents():
    return [S['park_x_mm'],*S['station_x_mm']]


def board_ports():
    return [(x,S['post_y_mm']+dy) for x in S['post_centers_x_mm'] for dy in S['foot_bolt_offsets_y_mm']]


def beam():
    p=base.box(*S['beam_bounds_mm']);xo,yo,zo=S['rail_origin_mm'];lo,hi=S['beam_bounds_mm'][-2:]
    for x,y in ((xo-8,yo),(xo+8,yo),(xo,yo-8),(xo,yo+8)):
        p=p.cut(base.cyl_z(lo-1,hi+1,1.7,x,y)).cut(base.hex_z(lo-1,S['beam_rail_nut_roof_mm'],5.8,x,y))
    for x in S['post_centers_x_mm']:
        p=p.cut(base.cyl_z(lo-1,hi+1,1.7,x,S['post_y_mm']))
        p=p.cut(base.cyl_z(S['beam_mount_screw_seat_mm'],hi+1,3,x,S['post_y_mm']))
    dx,dy=S['index_port_xy_mm']
    for x in detents():p=p.cut(base.cyl_z(S['index_beam_hole_bottom_mm'],hi+1,S['index_bore_mm']/2,x+dx,yo+dy))
    return p


def post():
    y=S['post_y_mm'];w=S['post_halfwidth_mm'];d=S['post_halfdepth_mm'];lo,hi=S['post_bottom_top_mm']
    p=base.box(-w,w,y-d,y+d,lo,hi)
    p=p.union(base.box(-S['foot_halfwidth_mm'],S['foot_halfwidth_mm'],y-S['foot_halfdepth_mm'],y+S['foot_halfdepth_mm'],lo,S['foot_top_mm']))
    for dy in S['foot_bolt_offsets_y_mm']:p=p.cut(base.cyl_z(lo-1,S['foot_top_mm']+1,1.7,0,y+dy))
    p=p.cut(base.cyl_z(S['post_upper_pilot_bottom_mm'],hi+1,1.7,0,y))
    a,b=S['post_upper_nut_floor_mm'],S['post_upper_nut_roof_mm']
    return p.cut(base.hex_z(a,b,5.8,0,y)).cut(base.box(0,w+1,y-3.4,y+3.4,a,b))


def rail():
    p=base.slide_base(S['rail_length_mm']);dx,dy=S['index_port_xy_mm'];xo=S['rail_origin_mm'][0]
    for x in detents():p=p.cut(base.cyl_z(-1,7,S['index_bore_mm']/2,x-xo+dx,dy))
    return p


def carriage():
    p=base.P;a=p['carriage_length']/2;w=S['carriage_width_mm']/2;f=p['floor_thickness'];h=f+S['carriage_flange_height_mm']
    c=base.box(-a,a,-w,w,f,h).union(base.box(-a,a,-p['neck_width']/2,p['neck_width']/2,h,p['carriage_top']))
    for x in (-8,8):c=c.cut(base.cyl_z(f-1,p['carriage_top']+1,1.7,x)).cut(base.hex_z(f-1,p['nut_pocket_roof'],5.8,x))
    dx,dy=S['index_port_xy_mm']
    return c.cut(base.cyl_z(f-1,p['carriage_top']+1,S['index_bore_mm']/2,dx,dy))


def carrier():
    a,b=S['carrier_face_u_mm'];v0,v1=S['carrier_face_v_mm'];w=S['carrier_face_half_w_mm']
    local=base.box(a,b,v0,v1,-w,w)
    pv,pw=S['key_head_pocket_vw_mm'];wall=S['key_head_boss_wall_mm']
    for roll in S['roll_detents_deg']:
        for ww in S['key_w_mm']:
            boss=base.box(b,b+S['key_head_boss_depth_mm'],S['key_v_mm']-pv/2-wall,S['key_v_mm']+pv/2+wall,ww-pw/2-wall,ww+pw/2+wall)
            hole=base.cyl_x(a-1,b+1,S['key_bore_mm']/2,S['key_v_mm'],ww)
            pocket=base.box(b,b+S['key_head_boss_depth_mm']+1,S['key_v_mm']-pv/2,S['key_v_mm']+pv/2,ww-pw/2,ww+pw/2)
            local=local.union(boss.rotate((0,0,0),(1,0,0),roll)).cut(hole.rotate((0,0,0),(1,0,0),roll)).cut(pocket.rotate((0,0,0),(1,0,0),roll))
    face=cq.Workplane(obj=transform(local.val(),0));p=face
    for height in S['dock_heights_mm'][1:]:p=p.union(face.translate((0,0,height)))
    for name in ('carrier_column_bounds_mm','carrier_beam_bounds_mm','carrier_bridge_bounds_mm','carrier_upper_bridge_bounds_mm','carrier_riser_bounds_mm'):p=p.union(base.box(*S[name]))
    for bounds in S['carrier_rib_bounds_mm']:p=p.union(base.box(*bounds))
    # Reapply every physical key hole after structural unions, so a rib cannot
    # accidentally fill a receiving hole or the antirotation head pocket.
    for height in S['dock_heights_mm']:
        for roll in S['roll_detents_deg']:
            for ww in S['key_w_mm']:
                hole=base.cyl_x(a-1,b+1,S['key_bore_mm']/2,S['key_v_mm'],ww)
                pocket=base.box(b,S['key_rear_access_end_u_mm'],S['key_v_mm']-pv/2,S['key_v_mm']+pv/2,ww-pw/2,ww+pw/2)
                for cutter in (hole,pocket):p=p.cut(cq.Workplane(obj=transform(cutter.val(),0,roll).translate((0,0,height))))
    yo=S['rail_origin_mm'][1]
    lo,hi=S['carrier_beam_bounds_mm'][-2:]
    for x in (-8,8):p=p.cut(base.cyl_z(lo-1,hi+1,1.7,x,yo)).cut(base.cyl_z(S['carrier_mount_seat_z_mm'],hi+1,3,x,yo))
    dx,dy=S['index_port_xy_mm']
    return p.cut(base.cyl_z(lo-1,hi+1,S['index_bore_mm']/2,dx,yo+dy))


def shoe():
    a,b=S['shoe_u_mm'];v0,v1=S['shoe_base_v_mm'];w=S['shoe_base_half_w_mm']
    p=base.box(a,b,v0,v1,-w,w).union(base.box(a,b,*S['shoe_stem_v_mm'],-S['shoe_stem_half_w_mm'],S['shoe_stem_half_w_mm']))
    # Relational nest on the fork's upper and two lateral edges. The mounting
    # screws supply retention, while these post-finished faces locate the shoe.
    I=json.loads((base.ROOT/'spec/transfer_interfaces.json').read_text());fw=I['fork_wing_outer_w_mm'];vt=I['fork_v_mm'][1];e=S['shoe_nest_clearance_mm'];depth=S['shoe_nest_depth_mm']
    p=p.union(base.box(a-depth,a,vt+e,v1,-w,w))
    for ww in I['frame_port_w_mm']:p=p.cut(base.cyl_x(a-1,b+1,I['frame_port_d_mm']/2,I['frame_port_v_mm'],ww))
    for ww in S['key_w_mm']:p=p.cut(base.cyl_x(a-1,b+1,S['key_bore_mm']/2,S['key_v_mm'],ww))
    return p


def key(diamond=False):
    length=S['key_shoulder_length_mm'];diam=S['key_shaft_d_mm'];v,w=S['key_head_vw_mm']
    p=base.cyl_x(0,length,diam/2)
    if diamond:
        hw=S['diamond_width_w_mm']/2
        for sign in (-1,1):
            z0,z1=sorted((sign*hw,sign*(diam/2+1)))
            p=p.cut(base.box(-1,S['diamond_length_mm'],-diam,diam,z0,z1))
    return p.union(base.cyl_x(-S['key_thread_length_mm'],0,S['key_thread_d_mm']/2)).union(base.box(length,length+S['key_head_height_mm'],-v/2,v/2,-w/2,w/2))


def drilled_board():
    p=base.base_board();height=base.S['frame']['base_size'][2]
    for x,y in board_ports():p=p.cut(base.cyl_z(-1,height+1,1.7,x,y))
    return p


def symmetric_part(name,relief):
    p=transfer_parts()[name];I=json.loads((base.ROOT/'spec/transfer_interfaces.json').read_text())
    _,u,origin=original.reference_frame();loc=cq.Location(cq.Plane(origin=tuple(origin),xDir=tuple(u),normal=(1,0,0)))
    margin=S['nonfunctional_relief_extra_margin_mm']
    bounds=[value+(-margin if j%2==0 else margin) for j,value in enumerate(I[relief])]
    cutter=base.box(*bounds).val().moved(loc.inverse).rotate((0,0,0),(1,0,0),-original.I['transfer_roll_deg'])
    return p.cut(cq.Workplane(obj=cutter)).cut(cq.Workplane(obj=cutter).mirror('XY'))


def index_pin():
    pin=base.FINISH['index_pin']
    return base.cyl_z(-S['index_pin_shaft_length_mm'],0,pin['shaft_d_mm']/2).union(base.cyl_z(0,pin['head_height_mm'],pin['head_d_mm']/2))


@lru_cache(maxsize=1)
def parts():
    return {'XT01_crossbeam':beam(),'XT02_upright':post(),'XT03_index_rail':rail(),'XT04_index_carriage':carriage(),
            'XT05_carrier':carrier(),'XT06_keyed_shoe':shoe(),'XT07_round_key':key(),'XT08_diamond_key':key(True),'XT09_drilled_base':drilled_board(),
            'XT10_lift_carriage':symmetric_part('R05_lift_carriage','verge_relief_global_box_mm'),
            'XT11_anchor':symmetric_part('R06_anchor','bank_relief_global_box_mm'),'XT12_index_pin':index_pin()}


def hardware(ps,x,roll,index_locked=True,dock_height=0):
    if dock_height not in S['dock_heights_mm']:raise ValueError('Transfer must seat on an authored physical dock')
    if roll not in S['roll_detents_deg']:raise ValueError('Transfer roll requires one of the two physical keyed patterns')
    xo,yo,zo=S['rail_origin_mm'];travel=(S['rail_length_mm']-2*base.P['endstop_thickness']-base.P['carriage_length'])/2
    if not math.isfinite(x)or abs(x-xo)>travel+1e-9:raise ValueError('Transfer carriage outside physical end stops')
    if index_locked and x not in detents():raise ValueError('Index pin cannot engage between drilled detents')
    if not index_locked and dock_height!=S['dock_heights_mm'][-1]:
        raise ValueError('X indexing requires the retained upper dock')
    p=parts();kind=S['rail_kind'];slides=dict(ps);slides['A01_'+kind+'_rail']=p['XT03_index_rail'];slides['A02_carriage']=p['XT04_index_carriage']
    local=base.add_slide_hardware(base.slide_instances(slides,x-xo,kind),x-xo,kind)
    local.pop('HW_M3x12_slide_lock');local.pop('HW_M3nut_slide_lock')
    scene=base.transformed(local,(xo,yo,zo),(1,0,0),(0,0,1),'XT_RAIL_')
    scene['XT01_crossbeam']=p['XT01_crossbeam'].val();scene['XT05_carrier']=p['XT05_carrier'].translate((x,0,0)).val()
    scene['XT06_keyed_shoe']=transform(p['XT06_keyed_shoe'].val(),x,roll).translate((0,0,dock_height))
    for j,xx in enumerate(S['post_centers_x_mm']):
        scene[f'XT02_upright_{j}']=p['XT02_upright'].translate((xx,0,0)).val()
        scene[f"XT_HW_M3x{S['beam_mount_screw_length_mm']}_beam_{j}"]=base.bolt(3,S['beam_mount_screw_length_mm']).translate((xx,S['post_y_mm'],S['beam_mount_screw_seat_mm'])).val()
        scene[f'XT_HW_M3nut_beam_{j}']=base.nut(3).translate((xx,S['post_y_mm'],S['post_upper_nut_roof_mm']-2.4)).val()
    for j,(xx,yy) in enumerate(board_ports()):
        scene[f'XT_HW_M3x25_base_{j}']=base.bolt(3,S['base_mount_screw_length_mm']).translate((xx,yy,S['foot_top_mm'])).val()
        scene[f'XT_HW_M3nut_base_{j}']=base.nut(3).translate((xx,yy,-2.4)).val()
    for j,(xx,yy) in enumerate(((xo-8,yo),(xo+8,yo),(xo,yo-8),(xo,yo+8))):
        scene[f'XT_HW_M3x14_rail_{j}']=base.bolt(3,S['rail_mount_screw_length_mm']).translate((xx,yy,zo+2.8)).val()
        scene[f'XT_HW_M3nut_rail_{j}']=base.nut(3).translate((xx,yy,S['beam_rail_nut_roof_mm']-2.4)).val()
    for j,dx in enumerate((-8,8)):scene[f"XT_HW_M3x{S['carrier_mount_screw_length_mm']}_carrier_{j}"]=base.bolt(3,S['carrier_mount_screw_length_mm']).translate((x+dx,yo,S['carrier_mount_seat_z_mm'])).val()
    dx,dy=S['index_port_xy_mm'];scene['XT12_index_pin']=p['XT12_index_pin'].translate((x+dx,yo+dy,S['index_pin_seat_z_mm']+(0 if index_locked else 38))).val()
    for j,ww in enumerate(S['key_w_mm']):
        keyname='XT07_round_key' if j==0 else 'XT08_diamond_key'
        scene[keyname]=transform(p[keyname].translate((S['shoe_u_mm'][0],S['key_v_mm'],ww)).val(),x,roll).translate((0,0,dock_height))
        nut=base.place(base.nut(2),(S['shoe_u_mm'][0],S['key_v_mm'],ww),(0,0,1),(-1,0,0))
        scene[f'XT_HW_M2nut_key_{j}']=transform(nut,x,roll).translate((0,0,dock_height))
    for j,ww in enumerate((-7,7)):
        bolt=base.place(base.bolt(3,original.I['fork_mount_screw_length_mm']),(original.I['fork_mount_screw_seat_u_mm'],original.I['frame_port_v_mm'],ww),(0,0,1),(-1,0,0))
        nut=base.place(base.nut(3),(original.I['fork_mount_nut_front_u_mm'],original.I['frame_port_v_mm'],ww),(0,0,1),(1,0,0))
        scene[f'XT_HW_M3x16_fork_{j}']=transform(bolt,x,roll).translate((0,0,dock_height));scene[f'XT_HW_M3nut_fork_{j}']=transform(nut,x,roll).translate((0,0,dock_height))
    return scene


def installed(ps,tp,station_index=1,transfer_x=None,roll=20,advance=0,gate=16.5,lift=0,reset=0,
              guide=None,head_tip=None,head_roll=None,support_q=None,support_gate_q=None,index_locked=True,dock_height=0,feed_mode='high',carrier_z=160):
    if type(station_index)is not int or not 0<=station_index<len(S['station_x_mm']):raise ValueError('Unknown physical support station')
    x=S['station_x_mm'][station_index] if transfer_x is None else float(transfer_x)
    ref,u,_=original.reference_frame();ref=ref.copy();ref[0]=S['station_x_mm'][station_index]
    tip=ref+advance*u if head_tip is None else np.asarray(head_tip,dtype=float)
    guide=S['guide_index_park_mm'] if guide is None else guide
    head_roll=roll if head_roll is None else head_roll
    if support_q is None:support_q=[25 if i==station_index else 0 for i in range(len(S['station_x_mm']))]
    scene=base.integrated_instances(ps,head_tip=tip.tolist(),guide_tip=guide,head_gate=gate,head_roll=head_roll,
            support_q=support_q,support_gate_q=[0]*4 if support_gate_q is None else support_gate_q,takedown_z=original.I['take_down_z_mm'],feed_mode=feed_mode,carrier_z=carrier_z)
    scene['F03_base_board']=parts()['XT09_drilled_base'].val()
    scene.pop('HW_M3x16_eye');length=original.I['fairlead_mount_screw_length_mm']
    scene[f'HW_M3x{length}_eye']=base.place(base.bolt(3,length),original.I['fairlead_mount_screw_underhead_xyz_mm'],(1,0,0),(0,1,0))
    for source,dest in [('H01_hook_body','H01_hook_body'),('H02_gate','H02_gate'),('TH_H03_barrel_stop','H03_barrel_stop')]:
        shape=tp[source].val()
        if source=='H02_gate':shape=shape.translate((-gate,0,0))
        shape=shape.rotate((0,0,0),(1,0,0),head_roll)
        scene['TOOL_'+dest]=base.transformed({'p':shape},tuple(tip-5*u),tuple(u),(1,0,0))['p']
    for name,obj in tp.items():
        if name.startswith('R'):
            if name=='R05_lift_carriage':obj=parts()['XT10_lift_carriage']
            if name=='R06_anchor':obj=parts()['XT11_anchor']
            scene['TRANSFER_'+name]=transform(obj.val().translate(motion_shift(name,advance,gate,lift,reset)),x,roll).translate((0,0,dock_height))
    scene.update(hardware(ps,x,roll,index_locked,dock_height))
    return scene


SERVICE_PHASES=('nuts_out','keys_out','withdraw','lift','rekey','seat','keys_reposition','keys_in','nuts_reposition','nuts_in')


def service_pose(scene,x,from_roll,to_roll,from_height,to_height,phase,fraction):
    """Actual manually supported empty-module service path, with all solids.

    `scene` is a seated source configuration. The detached keys and nuts remain
    explicit shapes. This function supplies rigid geometry, not an actuator,
    an admission of yarn custody, or a clearance certificate by itself.
    """
    if from_roll not in S['roll_detents_deg'] or to_roll not in S['roll_detents_deg']:
        raise ValueError('Service roll endpoints must be actual keyed positions')
    if from_height not in S['dock_heights_mm'] or to_height not in S['dock_heights_mm']:
        raise ValueError('Service heights must be physical docks')
    if x not in S['service_station_x_mm']:
        raise ValueError('Dock/rekey service requires a support station; park uses retained upper dock')
    for name,part in [('R05_lift_carriage',parts()['XT10_lift_carriage']),
                      ('R19_pin_shuttle',transfer_parts()['R19_pin_shuttle'])]:
        expected=transform(part.val().translate(motion_shift(name,0,0,S['service_lift_mm'],0)),x,from_roll).translate((0,0,from_height))
        if (scene['TRANSFER_'+name].Center()-expected.Center()).Length>1e-7:
            raise ValueError('Service requires the empty lift at its upper stop and reset at zero')
    if phase not in SERVICE_PHASES or not math.isfinite(fraction) or not 0<=fraction<=1:
        raise ValueError('Unknown service phase or fraction')
    # Each group is [roll, height, signed axial displacement].
    module=[from_roll,from_height,0.];keys=module.copy();nuts=module.copy()
    for name in SERVICE_PHASES[:SERVICE_PHASES.index(phase)+1]:
        t=fraction if name==phase else 1.
        if name=='nuts_out':nuts[2]=-S['nut_removal_mm']*t
        elif name=='keys_out':keys[2]=S['key_removal_mm']*t
        elif name=='withdraw':module[2]=-S['manual_withdrawal_mm']*t
        elif name=='lift':module[1]=from_height+(to_height-from_height)*t
        elif name=='rekey':module[0]=from_roll+(to_roll-from_roll)*t
        elif name=='seat':module[2]=-S['manual_withdrawal_mm']*(1-t)
        elif name=='keys_reposition':keys[:2]=[from_roll+(to_roll-from_roll)*t,from_height+(to_height-from_height)*t]
        elif name=='keys_in':keys[2]=S['key_removal_mm']*(1-t)
        elif name=='nuts_reposition':nuts[:2]=[from_roll+(to_roll-from_roll)*t,from_height+(to_height-from_height)*t]
        elif name=='nuts_in':nuts[2]=-S['nut_removal_mm']*(1-t)
    _,u,origin=original.reference_frame();origin=origin.copy();origin[0]=x;axis=origin+[0,0,from_height]
    out=dict(scene)
    for name,shape in scene.items():
        if name in ('XT07_round_key','XT08_diamond_key'):pose=keys
        elif name.startswith('XT_HW_M2nut_key_'):pose=nuts
        elif name.startswith(('TRANSFER_','XT_HW_M3x16_fork_','XT_HW_M3nut_fork_')) or name=='XT06_keyed_shoe':pose=module
        else:continue
        out[name]=shape.rotate(tuple(axis),tuple(axis+u),pose[0]-from_roll).translate(tuple((pose[1]-from_height)*np.array([0.,0.,1.])+pose[2]*u))
    return out
