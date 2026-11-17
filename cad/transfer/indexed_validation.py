"""Native rigid index/service checks, independent of yarn/force solvers.

A midpoint native distance minus a rigid point-travel bound certifies every
fraction of an accepted interval. Explicit analytic mating pairs need a native
swept-envelope witness; they are reported, never silently discarded.
"""
import itertools
import math
import numpy as np
from cad.transfer import indexed as i
b=i.base


def bounds(shape):
    z=shape.BoundingBox()
    return np.array([z.xmin,z.ymin,z.zmin]),np.array([z.xmax,z.ymax,z.zmax])


def box_distance(a,c):
    return float(np.linalg.norm(np.maximum(np.maximum(a[0]-c[1],c[0]-a[1]),0)))


def overlaps(scene,focus=lambda n:n.startswith(('XT','TRANSFER'))):
    boxes={n:bounds(s) for n,s in scene.items()};found=[]
    for a,c in itertools.combinations(scene,2):
        if not(focus(a)or focus(c)):continue
        if np.any(np.minimum(boxes[a][1],boxes[c][1])-np.maximum(boxes[a][0],boxes[c][0])<=1e-7):continue
        volume=scene[a].intersect(scene[c]).Volume()
        if volume>1e-6:found.append([a,c,float(volume)])
    return found


def certify(pose,moving,speed,witnesses=(),max_depth=14,coordinate_speed=None,
            required_clearance=0.,contact_pairs=()):
    """Certify nominal nonpenetration; no manufactured clearance is inferred."""
    if not math.isfinite(speed)or speed<0:raise ValueError('Finite nonnegative speed bound required')
    if not math.isfinite(required_clearance)or required_clearance<0:raise ValueError('Finite nonnegative clearance required')
    coordinate_speed=np.full(3,speed) if coordinate_speed is None else np.asarray(coordinate_speed,dtype=float)
    if coordinate_speed.shape!=(3,)or not np.all(np.isfinite(coordinate_speed))or np.any(coordinate_speed<0):
        raise ValueError('Finite nonnegative coordinate motion bounds required')
    source=pose(0);moving=set(moving);fixed={n:s for n,s in source.items() if n not in moving}
    boxes={n:bounds(s) for n,s in fixed.items()};allowed=set();proofs=[]
    for a,c,envelope in witnesses:
        volume=float(envelope.intersect(fixed[c]).Volume())
        if volume>1e-6:return {'certified':False,'failed_witness':[a,c,volume]}
        allowed.add((a,c));proofs.append({'moving':a,'fixed':c,'swept_overlap_mm3':volume,
                                        'swept_native_gap_mm':float(envelope.distance(fixed[c]))})
    queries=0;leaves=0;minimum=float('inf');cache={0.:source}
    def sample(fraction):
        if fraction not in cache:
            if len(cache)>32:cache.pop(next(iter(cache)))
            cache[fraction]=pose(fraction)
        return cache[fraction]
    # Pairwise interval trees avoid rechecking already-separated pairs every
    # time a close interface needs a finer motion bound.
    for name in sorted(moving):
        for other,solid in fixed.items():
            if (name,other)in allowed:continue
            required=0. if (name,other)in contact_pairs else required_clearance
            stack=[(0.,1.,0)]
            while stack:
                lo,hi,depth=stack.pop();mid=(lo+hi)/2;motion=speed*(hi-lo)/2
                shape=sample(mid)[name];bb=bounds(shape);extent=coordinate_speed*(hi-lo)/2
                signed_gap=np.maximum(bb[0]-extent-boxes[other][1],boxes[other][0]-bb[1]-extent)
                if np.max(signed_gap)>=required-1e-7:
                    minimum=min(minimum,float(max(0.,np.max(signed_gap))));leaves+=1;continue
                distance=float(shape.distance(solid));queries+=1
                if not math.isfinite(distance):raise ValueError('Nonfinite native distance')
                if distance<1e-8 and shape.intersect(solid).Volume()>1e-6:
                    return {'certified':False,'fraction':mid,'collision':[name,other],'queries':queries}
                if distance<required-1e-7:
                    return {'certified':False,'fraction':mid,'tight_pair':[name,other],
                            'native_gap_mm':distance,'required_clearance_mm':required,'queries':queries}
                bound=distance-motion
                if bound>=required-1e-7:minimum=min(minimum,bound);leaves+=1;continue
                if depth>=max_depth:
                    return {'certified':False,'unresolved_pair':[name,other],'interval':[lo,hi],'bound_mm':bound,'queries':queries}
                stack.extend([(lo,mid,depth+1),(mid,hi,depth+1)])
    if not math.isfinite(minimum):raise ValueError('Empty native certificate')
    return {'certified':True,'minimum_distance_bound_mm':minimum,'intervals':leaves,'native_queries':queries,
            'analytic_mate_witnesses':proofs,'numerical_tolerance_mm':1e-7,
            'nonmating_required_clearance_mm':required_clearance,'intentional_contact_pairs':list(contact_pairs),
            'scope':'Continuous native rigid bound; manufacturing admission additionally requires the documented error/fit budget. No textile, force or measured retention claim'}


def index_certificate(source,span,required_clearance=0.):
    moving={n for n in source if n.startswith(('TRANSFER_','XT_HW_M3x16_fork_','XT_HW_M3nut_fork_','XT_HW_M2nut_key_','XT_HW_M3x20_carrier_')) or n in ('XT05_carrier','XT06_keyed_shoe','XT07_round_key','XT08_diamond_key','XT12_index_pin','XT_RAIL_A02_carriage') or n.startswith('XT_RAIL_HW_M3nut_carriage_')}
    # Actual slide nut labels are detected from their rigid relation to the
    # moving carriage. All other indexed rail hardware remains fixed.
    moving.update(n for n in source if n.startswith('XT_RAIL_HW_M3nut_mount_'))
    x0=source['XT05_carrier'].Center().x-i.parts()['XT05_carrier'].val().Center().x
    a=b.P['carriage_length']/2;f=b.P['floor_thickness'];h=f+i.S['carriage_flange_height_mm'];z=i.S['rail_origin_mm'][2];y=i.S['rail_origin_mm'][1]
    lo=min(x0,x0+span)-a;hi=max(x0,x0+span)+a
    envelope=b.box(lo,hi,y-i.S['carriage_width_mm']/2,y+i.S['carriage_width_mm']/2,z+f,z+h).union(b.box(lo,hi,y-b.P['neck_width']/2,y+b.P['neck_width']/2,z+h,z+b.P['carriage_top'])).val()
    witnesses=[('XT_RAIL_A02_carriage',n,envelope) for n in source if n=='XT_RAIL_A01_gy_rail' or n.startswith(('XT_RAIL_A03_','XT_RAIL_A04_'))]
    # The shared rail-floor/socket-seat stack is an explicit post-finished
    # running fit, with its native swept gap and worst-case .165mm separately
    # recorded; whole-machine registration does not apply twice to that datum.
    witnesses.extend(('XT_RAIL_A02_carriage',n,envelope)for n in source if n.startswith('XT_HW_M3x14_rail_'))
    for name in moving:
        if name.startswith(('XT_RAIL_HW_M3nut_carriage_','XT_HW_M3x20_carrier_')):
            low,high=bounds(source[name]);low[0]+=min(0,span);high[0]+=max(0,span)
            sweep=b.box(low[0],high[0],low[1],high[1],low[2],high[2]).val()
            witnesses.extend((name,n,sweep) for n in source if n.startswith(('XT_RAIL_A01_','XT_RAIL_A03_','XT_RAIL_A04_','XT_RAIL_A05_','XT_RAIL_A06_')))
    def pose(fraction):return {n:s.translate((span*fraction,0,0)) if n in moving else s for n,s in source.items()}
    return certify(pose,moving,abs(span),witnesses,coordinate_speed=[abs(span),0,0],required_clearance=required_clearance)


def service_certificate(source,x,from_roll,to_roll,from_height,to_height,phase,required_clearance=0.):
    pose=lambda f:i.service_pose(source,x,from_roll,to_roll,from_height,to_height,phase,f)
    start,end=pose(0),pose(1)
    if phase.startswith('nuts_'):moving={n for n in source if n.startswith('XT_HW_M2nut_key_')}
    elif phase.startswith('keys_'):moving={'XT07_round_key','XT08_diamond_key'}
    else:moving={n for n in source if n.startswith(('TRANSFER_','XT_HW_M3x16_fork_','XT_HW_M3nut_fork_'))or n=='XT06_keyed_shoe'}
    angle=abs(to_roll-from_roll)*math.pi/180 if phase in ('rekey','keys_reposition','nuts_reposition') else 0
    height=abs(to_height-from_height) if phase in ('lift','keys_reposition','nuts_reposition')else 0
    axial=i.S['manual_withdrawal_mm'] if phase in ('withdraw','seat')else i.S['key_removal_mm'] if phase in ('keys_out','keys_in')else i.S['nut_removal_mm'] if phase in ('nuts_out','nuts_in')else 0
    _,u,origin=i.original.reference_frame();origin=origin.copy();origin[0]=x;origin[2]+=from_height
    radius=0
    for n in moving:
        low,high=bounds(start[n]);radius=max(radius,max(np.linalg.norm(np.cross(np.array(p)-origin,u)) for p in itertools.product(*zip(low,high))))
    speed=axial+height+radius*angle;witnesses=[]
    if phase in ('keys_out','keys_in'):
        roll,height0=(from_roll,from_height)if phase=='keys_out'else(to_roll,to_height)
        length=i.S['key_shoulder_length_mm'];d=i.S['key_removal_mm'];v,w=i.S['key_head_vw_mm']
        for n,ww in zip(('XT07_round_key','XT08_diamond_key'),i.S['key_w_mm']):
            envelope=b.cyl_x(-i.S['key_thread_length_mm'],length+d,i.S['key_shaft_d_mm']/2).union(b.box(length,length+i.S['key_head_height_mm']+d,-v/2,v/2,-w/2,w/2))
            envelope=i.transform(envelope.translate((i.S['shoe_u_mm'][0],i.S['key_v_mm'],ww)).val(),x,roll).translate((0,0,height0))
            witnesses.extend((n,c,envelope)for c in ('XT05_carrier','XT06_keyed_shoe'))
    if phase in ('nuts_out','nuts_in'):
        roll,height0=(from_roll,from_height)if phase=='nuts_out'else(to_roll,to_height)
        for j,ww in enumerate(i.S['key_w_mm']):
            length=i.S['nut_removal_mm']+b.S['fasteners']['M2']['nut_height_max'];af=b.S['fasteners']['M2']['nut_af_max']
            envelope=b.hex_z(0,length,af).cut(b.cyl_z(-1,length+1,1))
            envelope=b.place(envelope,(i.S['shoe_u_mm'][0],i.S['key_v_mm'],ww),(0,0,1),(-1,0,0))
            envelope=i.transform(envelope,x,roll).translate((0,0,height0))
            witnesses.append((f'XT_HW_M2nut_key_{j}',('XT07_round_key','XT08_diamond_key')[j],envelope))
    coordinate_speed=np.abs(u)*axial+np.array([0,0,height])+radius*angle
    contacts=[]
    if phase in ('withdraw','seat'):contacts.append(('XT06_keyed_shoe','XT05_carrier'))
    if phase in ('nuts_out','nuts_in'):contacts.extend((f'XT_HW_M2nut_key_{j}','XT06_keyed_shoe')for j in (0,1))
    return certify(pose,moving,speed,witnesses,coordinate_speed=coordinate_speed,
                   required_clearance=required_clearance,contact_pairs=contacts)


def tool_access_certificate(scene,x,roll,dock_height,key_index,kind):
    """Exact conservative axial sweeps for the selected manual bench tools.

    The pushrod and its targeted key share a flat endpoint throughout motion;
    that one intended tool/workpiece pair is reported explicitly. The complete
    key motion is separately certified by service_certificate, with all hardware.
    """
    a=i.S['shoe_u_mm'][0];vv=i.S['key_v_mm'];ww=i.S['key_w_mm'][key_index]
    ignored=[]
    if kind=='nutdriver':
        d=i.S['nut_removal_mm'];tool=i.S['service_tools']['nut_driver'];shaft=tool['blade_length_mm'];length=tool['overall_length_mm'];r=tool['chosen_receiving_blade_outer_d_max_mm']/2;rh=tool['chosen_receiving_handle_d_max_mm']/2
        envelope=b.cyl_x(a-shaft-d,a,r,vv,ww).union(b.cyl_x(a-length-d,a-shaft,rh,vv,ww)).cut(b.cyl_x(a-5,a+.01,2.5,vv,ww)).val()
        # The nut rides in the socket; its own motion is checked separately.
        # The socket nose/cavity conservatively admits its exact retained nut.
    elif kind in ('pushrod_front','pushrod_rear'):
        rod=i.S['service_tools']['key_pushrod'];length=rod['finished_length_mm'];radius=rod['finished_d_mm']/2;d=i.S['key_removal_mm']
        if kind=='pushrod_front':lo=a-i.S['key_thread_length_mm']-length;hi=a-i.S['key_thread_length_mm']+d
        else:lo=a+i.S['key_shoulder_length_mm']+i.S['key_head_height_mm'];hi=lo+d+length
        envelope=b.cyl_x(lo,hi,radius,vv,ww).val()
        scene=i.service_pose(scene,x,roll,roll,dock_height,dock_height,'keys_out',1)
        ignored=[('XT07_round_key','XT08_diamond_key')[key_index]]
    else:raise ValueError('Unknown selected service tool')
    envelope=i.transform(envelope,x,roll).translate((0,0,dock_height));bb=bounds(envelope);hits=[];queries=0;minimum=float('inf')
    for name,shape in scene.items():
        if name in ignored:continue
        other=bounds(shape)
        if np.any(np.minimum(bb[1],other[1])-np.maximum(bb[0],other[0])<=1e-7):continue
        queries+=1;volume=float(envelope.intersect(shape).Volume())
        if volume>1e-6:hits.append([name,volume])
    return {'certified':not hits,'kind':kind,'key_index':key_index,'native_queries':queries,'collisions':hits,
            'intentional_tool_workpiece_contact':ignored,'scope':'Exact conservative tool swept volume versus all other installed solids; targeted key endpoint is an explicit moving mate, key travel separately certified; operator hand is not modeled'}


def guide_x_certificate(source,target):
    """Bound actual guide X repositioning with other command values held fixed."""
    moving=set();delta=None
    for name,shape in source.items():
        shift=np.array(target[name].Center().toTuple())-shape.Center().toTuple()
        if np.linalg.norm(shift)<1e-7:continue
        if not name.startswith('GUIDE_')or np.linalg.norm(shift[1:])>1e-7:raise ValueError('Expected guide-only X translation')
        if delta is None:delta=shift
        if np.linalg.norm(shift-delta)>1e-7:raise ValueError('Guide members do not share rigid X translation')
        moving.add(name)
    if delta is None:raise ValueError('No guide X movement')
    name='GUIDE_X_A02_carriage';low,high=bounds(source[name]);low[0]+=min(0,delta[0]);high[0]+=max(0,delta[0]);yc=(low[1]+high[1])/2
    split=low[2]+b.P['carriage_flange_height']
    envelope=b.box(low[0],high[0],low[1],high[1],low[2],split).union(b.box(low[0],high[0],yc-b.P['neck_width']/2,yc+b.P['neck_width']/2,split,high[2])).val()
    fixedrail=[n for n in source if n.startswith(('GUIDE_X_A01_','GUIDE_X_A03_','GUIDE_X_A04_','GUIDE_X_A05_','GUIDE_X_A06_'))]
    witnesses=[(name,n,envelope)for n in fixedrail]
    for name in moving:
        if name.startswith(('GUIDE_X_HW_M3nut_carriage_','GUIDE_HW_M3x12_XY_')):
            low,high=bounds(source[name]);low[0]+=min(0,delta[0]);high[0]+=max(0,delta[0]);envelope=b.box(low[0],high[0],low[1],high[1],low[2],high[2]).val()
            witnesses.extend((name,n,envelope)for n in fixedrail)
    pose=lambda f:{n:s.translate(tuple(delta*f))if n in moving else s for n,s in source.items()}
    return certify(pose,moving,float(np.linalg.norm(delta)),witnesses,coordinate_speed=abs(delta))


def guide_yz_certificate(source,target,axis):
    if axis not in ('y','z'):raise ValueError('Expected guide Y or Z move')
    coordinate='xyz'.index(axis);moving=set();delta=None
    for name,shape in source.items():
        shift=np.array(target[name].Center().toTuple())-shape.Center().toTuple()
        if np.linalg.norm(shift)<1e-7:continue
        off=shift.copy();off[coordinate]=0
        if not name.startswith('GUIDE_')or np.linalg.norm(off)>1e-7:raise ValueError('Unexpected guide motion')
        if delta is None:delta=shift
        if np.linalg.norm(shift-delta)>1e-7:raise ValueError('Nonrigid guide group')
        moving.add(name)
    if delta is None:raise ValueError('No guide motion')
    prefix='GUIDE_'+axis.upper()+'_';name=prefix+'A02_carriage';low,high=bounds(source[name]);low[coordinate]+=min(0,delta[coordinate]);high[coordinate]+=max(0,delta[coordinate]);xc=(low[0]+high[0])/2
    if axis=='y':
        split=low[2]+b.P['carriage_flange_height']
        envelope=b.box(low[0],high[0],low[1],high[1],low[2],split).union(b.box(xc-b.P['neck_width']/2,xc+b.P['neck_width']/2,low[1],high[1],split,high[2])).val()
    else:
        split=high[1]-b.P['carriage_flange_height']
        envelope=b.box(low[0],high[0],split,high[1],low[2],high[2]).union(b.box(xc-b.P['neck_width']/2,xc+b.P['neck_width']/2,low[1],split,low[2],high[2])).val()
    fixedrail=[n for n in source if n.startswith(tuple(prefix+k for k in ('A01_','A03_','A04_','A05_','A06_')))]
    witnesses=[(name,n,envelope)for n in fixedrail]
    bolt_prefix='GUIDE_HW_M3x12_bracket_'if axis=='y'else'GUIDE_HW_M3x12_adapter_'
    for name in moving:
        if name.startswith((prefix+'HW_M3nut_carriage_',bolt_prefix)):
            low,high=bounds(source[name]);low[coordinate]+=min(0,delta[coordinate]);high[coordinate]+=max(0,delta[coordinate]);envelope=b.box(low[0],high[0],low[1],high[1],low[2],high[2]).val()
            witnesses.extend((name,n,envelope)for n in fixedrail)
    pose=lambda f:{n:s.translate(tuple(delta*f))if n in moving else s for n,s in source.items()}
    return certify(pose,moving,float(np.linalg.norm(delta)),witnesses,coordinate_speed=abs(delta))
