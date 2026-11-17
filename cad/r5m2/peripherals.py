"""Dimensioned manual feed, hanging clamp and plywood stand. Millimetres.
Geometry is nominal; weights, friction, stiffness and yarn retention require tests.
"""

def parts(c):
    b,cx,cy,cz,hz,hy=c.box,c.cyl_x,c.cyl_y,c.cyl_z,c.hex_z,c.hex_y
    p={}; S=c.S
    for i,(lo,hi) in enumerate(S['stand']['side_x_ranges']):
        q=b(lo,hi,10,470,-408,-8)
        for y in (20,460):
            x=(lo+hi)/2
            q=q.cut(cz(-16,-7,1.7,x,y)).cut(hz(-14,-11.6,5.8,x,y))
            q=q.cut(b(lo-1,x if i==0 else hi+1,y-3.4,y+3.4,-14,-11.6) if i==0 else b(x,hi+1,y-3.4,y+3.4,-14,-11.6))
        for z in (-60,-340):q=q.cut(cx(lo-1,hi+1,1.7,442,z))
        p[f'S0{i+1}_side']=q
    q=b(29,291,452,470,-408,-8)
    for x in (39,281):
        for z in (-60,-340):q=q.cut(cy(451,471,1.7,x,z))
    p['S03_back']=q
    q=b(0,4,0,20,0,20).union(b(0,20,16,20,0,20))
    q=q.cut(cx(-1,5,1.7,10,10)).cut(cy(15,21,1.7,10,10))
    p['S04_bracket_L']=q;p['S05_bracket_R']=q.mirror('YZ').translate((20,0,0))
    C=S['cloth_clamp']; half=C['closed_face_gap_mm']/2; pad=half+C['pad_thickness_mm']; outer=pad+C['jaw_thickness_mm']; h=C['body_height_mm']/2
    jaw=b(-C['body_width_mm']/2,C['body_width_mm']/2,-outer,-pad,-h,h)
    for x in C['bolt_x_mm']:jaw=jaw.cut(cy(-outer-1,-pad+1,C['bolt_clearance_radius_mm'],x,0))
    pad_shape=b(-C['pad_width_mm']/2,C['pad_width_mm']/2,-pad,-half,-h,h)
    if C.get('return_pin'):
        pin=C['return_pin'];px,py,pz=pin['center_body_mm'];socket=cy(pin['socket_back_y_mm'],-half+1,pin['socket_diameter_mm']/2,px,pz);jaw=jaw.cut(socket);pad_shape=pad_shape.cut(socket)
        p['D03_return_pin']=cy(-pin['length_mm']/2,pin['length_mm']/2,pin['diameter_mm']/2,px,pz)
    p['D01_jaw']=jaw;p['D02_pad']=pad_shape
    q=b(*S['feeder']['tower_bbox']);q=q.cut(b(32,64,415,423,110,210))
    for x,z in [(20,32),(76,32),(32,230),(64,230),(78,238),(76,256),(48,220),(16,235.5),(56,250),(28,155.5)]+[(x+6,z) for x in (24,72) for z in (120,200)]:q=q.cut(cy(415,423,1.7,x,z))
    for x in (24,72):
        for z in (120,200):q=q.cut(b(x-7.1,x-2.9,415,423,z-2.1,z+2.1))
    p['P01_tower']=q
    q=b(-10,10,395,416,-5,5).union(b(-7,-3,416,422,-2,2))
    q=q.cut(cz(-4,6,1.6,0,400)).cut(cy(394,423,1.7,6,0)).cut(hy(394,400,5.8,6,0))
    p['P02_lower_block']=q;p['P03_upper_block']=q.mirror('XY')
    C=S['feeder']['carrier_geometry']
    q=b(*C['bbox']).cut(b(*C['front_relief'])).union(b(*C['anchor_stem'])).union(b(*C['anchor_bbox']))
    for window in C['lightening_windows']:q=q.cut(b(*window))
    for x in S['feeder']['rod_x']:q=q.cut(cz(-4,4,C['rod_bore_radius'],x,400))
    q=q.cut(cy(409,415,C['axle_bore_radius'],48,0)).cut(cx(45,51,C['anchor_hole_radius'],C['anchor_y'],C['anchor_hole_z']))
    R=S['feeder']['pulley_head_reliefs']
    q=q.cut(cy(*R['y'],R['outer_radius'],48,0).cut(cy(409,413,R['inner_radius'],48,0)))
    p['P04_carrier']=q
    q=cz(-3,0,10).cut(cz(-1.5,1,11).cut(cz(-2,2,8)))
    q=q.cut(cz(-4,1,4.3)).cut(cz(-2.1,1,5.1))
    for x in (-6.5,6.5):q=q.cut(cz(-4,1,1.1,x))
    p['P05_pulley_half']=q
    p['P06_623_bearing_envelope']=cz(-2,2,5).cut(cz(-3,3,1.5))
    for name,L in [('P07_spacer4',4),('P08_spacer14',14),('P09_spacer7',7),('P19_spacer8',8),('P21_spacer2',2)]:p[name]=cz(0,L,2.4).cut(cz(-1,L+1,1.6))
    q=b(76,106,410,416,234,242).union(b(98,106,402,416,234,242))
    q=q.cut(cx(97,107,3.1,406,238)).cut(cy(409,417,1.7,78,238)).cut(hy(409,412.4,5.8,78,238))
    p['P10_fairlead_bracket']=q
    p['P11_fairlead']=cx(97,107,3,406,238).cut(cx(96,108,1.5,406,238))
    q=b(-8,8,422,442,12,18).union(b(-8,8,422,428,18,42))
    p['P12_foot']=q.cut(cz(11,19,1.7,0,434)).cut(cy(421,429,1.7,0,32))
    q=b(14,26,401,411,232,238).union(b(14,26,411,416,232,241))
    q=q.cut(cy(400,417,1.7,20,235.5)).cut(hy(411,414,5.8,20,235.5)).cut(b(13,21,411,414,232.5,238.5))
    upper=b(14,26,401,411,239.6,243.6); pad=b(14,26,401,411,238,238.5)
    for x in (17,23):
        q=q.cut(cz(231,239,1.1,x,409));upper=upper.cut(cz(239,245,1.1,x,409));pad=pad.cut(cz(237,240,1.1,x,409))
    p['P13_nip_lower']=q.translate((-4,0,0));p['P14_nip_upper']=upper.translate((-4,0,0));p['P15_nip_pad']=pad.translate((-4,0,0))
    q=b(*S['feeder']['idler_bracket_bbox']).cut(cy(409,417,1.7,88,250)).cut(cy(409,417,1.7,76,256)).cut(hy(409,412.4,5.8,76,256))
    q=q.cut(cy(*R['y'],R['outer_radius'],88,250).cut(cy(409,413,R['inner_radius'],88,250)))
    p['P16_idler_bracket']=q
    p['P17_park_cleat']=b(42,54,402,416,212,224).cut(cx(41,55,1,406,216)).cut(cy(401,417,1.7,48,220))
    p['P18_weight_cup']=cz(-12.5,12.5,6).cut(cz(-10.5,13,5)).cut(cy(-7,7,1,0,10))
    p['P20_rod']=cz(116,204,1.5,0,400)
    return p

def add(items,ps,c,carrier_z=160,takedown_z=50,mode='high',support_pin=False):
    def obj(name,key=None,xyz=(0,0,0),mirror=None):
        p=ps[name];p=p.mirror(mirror) if mirror else p
        items[key or name]=p.translate(xyz).val()
    def screw(name,d,L,at,n=(0,0,1),xd=(1,0,0)):items[name]=c.place(c.bolt(d,L),at,xd,n)
    def nut(name,d,at,n=(0,0,1),xd=(1,0,0)):items[name]=c.place(c.nut(d),at,xd,n)
    for name in ('S01_side','S02_side','S03_back'):obj(name)
    for i,(x,y) in enumerate(c.S['frame']['foot_centers']):
        items.pop(f'HW_M3x16_foot_{i}',None);items.pop(f'HW_M3nut_foot_{i}',None)
        screw(f'HW_M3x25_stand_top_{i}',3,25,(x,y,10));nut(f'HW_M3nut_stand_top_{i}',3,(x,y,-14))
    for side,x in [('L',29),('R',271)]:
        for j,z in enumerate((-70,-350)):
            obj('S04_bracket_L' if side=='L' else 'S05_bracket_R',f'S_bracket_{side}_{j}',(x,432,z))
            screw(f'HW_M3x30_stand_side_{side}_{j}',3,30,(33 if side=='L' else 287,442,z+10),(1,0,0) if side=='L' else (-1,0,0),(0,1,0))
            nut(f'HW_M3nut_stand_side_{side}_{j}',3,(8.6 if side=='L' else 309,442,z+10),(1,0,0),(0,1,0))
            screw(f'HW_M3x30_stand_back_{side}_{j}',3,30,(x+10,448,z+10),(0,-1,0))
            nut(f'HW_M3nut_stand_back_{side}_{j}',3,(x+10,470,z+10),(0,1,0))
    for side in ('A','B'):
        for name in ('D01_jaw','D02_pad'):obj(name,name+'_'+side,(150,165,takedown_z),'XZ' if side=='B' else None)
    C=c.S['cloth_clamp']; outer=C['closed_face_gap_mm']/2+C['pad_thickness_mm']+C['jaw_thickness_mm']
    if C.get('return_pin'):obj('D03_return_pin',xyz=(150,165,takedown_z))
    for i,x in enumerate(C['bolt_x_mm']):
        screw(f'HW_M3x16_cloth_{i}',3,16,(150+x,165-outer,takedown_z),(0,-1,0));nut(f'HW_M3nut_cloth_{i}',3,(150+x,165+outer,takedown_z),(0,1,0))
    for name in ('P01_tower','P10_fairlead_bracket','P11_fairlead','P13_nip_lower','P14_nip_upper','P16_idler_bracket','P17_park_cleat'):obj(name)
    obj('P15_nip_pad','P15_pad_lower');obj('P15_nip_pad','P15_pad_upper',(0,0,1.1))
    for i,x in enumerate((13,19)):
        screw(f'HW_M2x16_nip_{i}',2,16,(x,409,243.6));nut(f'HW_M2nut_nip_{i}',2,(x,409,230.4))
    for x,z,label in [(78,238,'eye'),(76,256,'idler'),(16,235.5,'nip')]:
        screw('HW_M3x16_'+label,3,16,(x,422,z),(0,1,0));nut('HW_M3nut_'+label,3,(x,410 if label!='nip' else 411,z),(0,1,0))
    screw('HW_M3x30_cleat',3,30,(48,402,220),(0,-1,0));nut('HW_M3nut_cleat',3,(48,422,220),(0,1,0))
    for i,x in enumerate((20,76)):
        obj('P12_foot',f'P12_foot_{i}',(x,0,0))
        screw(f'HW_M3x25_feedfoot_{i}',3,25,(x,434,18));nut(f'HW_M3nut_feedfoot_{i}',3,(x,434,-2.4))
        screw(f'HW_M3x16_tower_{i}',3,16,(x,416,32),(0,-1,0));nut(f'HW_M3nut_tower_{i}',3,(x,428,32),(0,1,0))
    for i,x in enumerate((24,72)):
        obj('P20_rod',f'P20_rod_{i}',(x,0,0))
        for z,name in [(120,'P02_lower_block'),(200,'P03_upper_block')]:
            obj(name,name+f'_{i}',(x,0,z))
            screw(f'HW_M3x25_rod_{i}_{z}',3,25,(x+6,422,z),(0,1,0));nut(f'HW_M3nut_rod_{i}_{z}',3,(x+6,397.6,z),(0,1,0))
    obj('P04_carrier',xyz=(0,0,carrier_z))
    from physics.r5_feed_geometry import counter_center
    f=c.S['feeder'];g=f['cord_geometry'];R=f['pulley_groove_radius']+f['rope_d']/2
    anchor=f['park_anchor'][2] if mode=='high' else carrier_z+g['main_eye_above_center_mm']
    cw=counter_center(anchor,f['rope_geometric_length_mm'],R,g)
    obj('P18_weight_cup',xyz=(96,406,cw))
    if support_pin:
        pin=c.S['feeder']['mode_support_pin']
        screw('HW_M3x25_mode_support',3,25,tuple(pin['underhead']),tuple(pin['normal']))
    for label,x,z,spacer,L,nuty in [('left',32,230,'P19_spacer8',30,422),('right',64,230,'P19_spacer8',30,422),('moving',48,carrier_z,'P21_spacer2',20,c.S['feeder']['carrier_geometry']['axle_nut_y']),('counter',88,250,'P21_spacer2',25,416),('lead',56,250,'P19_spacer8',30,422)]:
        for half in (0,1):
            p=ps['P05_pulley_half'];p=p.mirror('XY') if half else p
            items[f'P05_{label}_{half}']=c.place(p,(x,406,z),(1,0,0),(0,1,0))
        for name,at in [('P06_623_bearing_envelope',(x,406,z)),('P07_spacer4',(x,400,z)),(spacer,(x,408,z))]:items[f'{name}_{label}']=c.place(ps[name],at,(1,0,0),(0,1,0))
        screw(f'HW_M3x{L}_axle_{label}',3,L,(x,400,z),(0,-1,0));nut(f'HW_M3nut_axle_{label}',3,(x,nuty,z),(0,1,0))
        for j,dx in enumerate((-6.5,6.5)):
            screw(f'HW_M2x8_pulley_{label}_{j}',2,8,(x+dx,409,z),(0,1,0));nut(f'HW_M2nut_pulley_{label}_{j}',2,(x+dx,401.4,z),(0,1,0))
    return items
