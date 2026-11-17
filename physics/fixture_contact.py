"""Conservative box unions for actual support and cloth-clamp solids.
Holes are conservatively filled. Native shape-minus-envelope audits must bound
any omitted details. This is contact geometry, not a material strength model.
"""
import numpy as np
from physics.auxiliary_contact import box_distance3d
from physics.edge_contact import edge_samples
from physics.rigid_clamp import rotation
from physics.guide_contact import annular_cylinder

class BoxUnion:
    def __init__(self,boxes):
        self.boxes=[(np.asarray(a),np.asarray(b))for a,b in boxes]
        self.lo=np.min([a for a,b in self.boxes],axis=0);self.hi=np.max([b for a,b in self.boxes],axis=0)
    def distance(self,p):
        d=np.full(len(p),np.inf);g=np.zeros_like(p)
        for lo,hi in self.boxes:
            v,n=box_distance3d(p,lo,hi);mask=v<d;d[mask]=v[mask];g[mask]=n[mask]
        return d,g
    def edge_contact_terms(self,q,rest,counts,radius):
        e,t,w,p=edge_samples(q,rest,counts,self.lo,self.hi,radius)
        if len(e):
            d,g=self.distance(p);yield e,t,w,d,g

def bank_boxes(spec):
    B=spec['support_bank'];P=spec['slide'];ox,oy,oz=B['bank_origin'];W=B['bank_width'];L=B['bank_length'];front=oy-L/2+B.get('bank_front_relief_depth_mm',0.);back=oy+L/2;floor=oz+B['bank_floor'];top=oz+B['bank_top'];cap=top+B['bank_cap_thickness'];tie=P['endstop_thickness'];relief=B['cover_bed_relief_clearance'];left=ox-W/2;right=ox+W/2
    bed=[([left,front,oz],[right,back,floor])];cover=[]
    for width,zlo,zhi,ylo,yhi,dest in [(P['channel_width'],floor,top,front+tie+relief,back-tie-relief,bed),(B['bank_cap_slot_width'],top,cap,front,back,cover)]:
        cuts=[(B['first_station_x']+i*B['station_pitch']-width/2,B['first_station_x']+i*B['station_pitch']+width/2)for i in range(B['station_count'])];x=left
        for a,b in cuts:
            if a>x:dest.append(([x,ylo,zlo],[a,yhi,zhi]))
            x=b
        if right>x:dest.append(([x,ylo,zlo],[right,yhi,zhi]))
    cover.extend([([left,front,floor],[right,front+tie,cap]),([left,back-tie,floor],[right,back,cap])])
    return bed,cover

def clamp_pad_boxes(spec):
    """Cover rounded-window pads by boxes, retaining all four corner squares.

    The removed cross is INSIDE the native rounded rectangle. Filling its
    corner squares and spacer holes adds material, never omits native material.
    """
    g=spec['closed_face_gap_mm']/2;p=g+spec['pad_thickness_mm']
    w=spec['pad_width_mm']/2;h=spec['body_height_mm']/2
    window=spec.get('free_wrap_window');rects=[(-w,w,-h,h)]
    if window:
        x0,x1=window['x_mm'];z0,z1=window['z_mm'];r=window['corner_radius_mm']
        if not (-w<x0<x1<w and -h<z0<z1<h and 0<=2*r<min(x1-x0,z1-z0)):
            raise ValueError('Invalid clamp pad window')
        rects=[(-w,x0,-h,h),(x1,w,-h,h),(x0,x1,-h,z0),(x0,x1,z1,h)]
        if r:
            rects += [(a,b,c,d) for a,b in [(x0,x0+r),(x1-r,x1)]
                      for c,d in [(z0,z0+r),(z1-r,z1)]]
    return [([a,yl,c],[b,yh,d]) for yl,yh in [(-p,-g),(g,p)] for a,b,c,d in rects]


def subtract_box(box,cut):
    """Exact disjoint box decomposition of box minus an axis-aligned cutter."""
    lo,hi=[np.asarray(v,dtype=float)for v in box];a=np.maximum(lo,cut[0]);b=np.minimum(hi,cut[1])
    if np.any(a>=b):return [(lo,hi)]
    pieces=[]
    for axis in range(3):
        low=lo.copy();high=hi.copy();high[axis]=a[axis]
        if np.all(high>low):pieces.append((low,high))
        low=lo.copy();high=hi.copy();low[axis]=b[axis]
        if np.all(high>low):pieces.append((low,high))
        lo=lo.copy();hi=hi.copy();lo[axis]=a[axis];hi[axis]=b[axis]
    return pieces


class ClampContact(BoxUnion):
    """Clamp solids plus explicitly registered, bounded ideal-grip reductions.

    The edge-specific obstacle remains 1-Lipschitz: a grip removes only a box
    from the PAD cover by exact box decomposition. No pointwise mask is used.
    Jaws, pin and hardware remain active for every material edge.
    """
    def __init__(self,spec,center,angles,fixed_section=None):
        self.spec=spec;g=spec['closed_face_gap_mm']/2;p=g+spec['pad_thickness_mm'];o=p+spec['jaw_thickness_mm'];h=spec['body_height_mm']/2;w=spec['body_width_mm']/2
        self.pad_outer=p
        rigid=[([-w,-o,-h],[w,-p,h]),([-w,p,-h],[w,o,h])]
        for x in spec['bolt_x_mm']:
            flat=spec.get('front_fastener')
            length=(flat['overall_length_mm']+flat['length_tolerance_mm']+flat['seated_recess_range_mm'][1]) if flat else 16.
            rigid.extend([([x-1.5,-o,-1.5],[x+1.5,length-o,1.5]),([x-3.2,o,-3.2],[x+3.2,o+2.4,3.2])])
            # A qualified flush cone is wholly inside the conservative jaw box.
            # Old socket heads protrude beyond that box and must be retained.
            if not flat:rigid.append(([x-2.84,-o-3,-2.84],[x+2.84,-o,2.84]))
        self.rigid=BoxUnion(rigid);self.pads=BoxUnion(clamp_pad_boxes(spec))
        self.spacers=[];envelopes=list(rigid)+list(self.pads.boxes)
        spacer=spec.get('stop_spacer')
        if spacer:
            for x in spec['bolt_x_mm']:
                center_s=np.array([x,0.,0.]);length=spacer['length_mm'];ro=spacer['od_mm']/2
                self.spacers.append((center_s,length,spacer['bore_mm']/2,ro))
                envelopes.append((center_s+[-ro,-length/2,-ro],center_s+[ro,length/2,ro]))
        pin=spec.get('return_pin')
        if pin:
            pc=np.asarray(pin['center_body_mm']);pr=pin['diameter_mm']/2;pl=pin['length_mm']/2
            envelopes.append((pc+[-pr,-pl,-pr],pc+[pr,pl,pr]))
        super().__init__(envelopes)
        self.local_lo=self.lo.copy();self.local_hi=self.hi.copy()
        self.radius=float(np.linalg.norm(np.maximum(abs(self.local_lo),abs(self.local_hi))))
        self.set_gripped_edges(fixed_section);self.set_pose(center,angles)

    def set_gripped_edges(self,fixed_section):
        self.grip_regions={};self.reduced_pads={}
        if not fixed_section or not fixed_section.get('gripped_edges'):
            return
        grips=self.spec.get('grips')
        if not grips:raise ValueError('Gripped edges require physical grip specification')
        transition=float(grips['exit_transition_mm'])
        if not 0<transition<=.35:raise ValueError('Grip transition must be in (0,0.35] mm')
        indices=fixed_section['indices'];body=np.asarray(fixed_section['body_xyz_mm'],dtype=float)
        if body.shape!=(len(indices),3) or not np.all(np.isfinite(body)) or len(set(indices))!=len(indices):
            raise ValueError('Invalid fixed grip material coordinates')
        positions=dict(zip(indices,body));edges=fixed_section['gripped_edges']
        if len(set(edges))!=len(edges) or any(type(e) is not int or e<0 for e in edges):
            raise ValueError('Gripped edge IDs must be unique nonnegative integers')
        lanes=np.asarray([grips['first_x_mm'],*grips['return_x_mm']]);z0,z1=grips['land_z_mm']
        error=float(grips['setting_position_uncertainty_mm'])
        for edge in edges:
            if edge not in positions or edge+1 not in positions:
                raise ValueError('A gripped edge must have two prescribed material endpoints')
            ends=np.array([positions[edge],positions[edge+1]])
            lane_dist=np.max(abs(ends[:,0,None]-lanes),axis=0)
            if (np.min(lane_dist)>error+1e-12 or np.max(abs(ends[:,1]))>error+1e-12
                    or np.min(ends[:,2])<z0-transition-1e-12 or np.max(ends[:,2])>z1+transition+1e-12):
                raise ValueError('Gripped edge lies outside a physical grip land/exit transition')
            lo=ends.min(axis=0)-[transition,0.,transition]
            hi=ends.max(axis=0)+[transition,0.,transition]
            # Do not extend beyond the admitted 0.35 mm transition at either end.
            lo[2]=max(lo[2],z0-transition);hi[2]=min(hi[2],z1+transition)
            lo[1]=-self.pad_outer;hi[1]=self.pad_outer
            self.grip_regions[edge]=(lo,hi)
            pieces=[part for box in self.pads.boxes for part in subtract_box(box,(lo,hi))]
            self.reduced_pads[edge]=BoxUnion(pieces)

    def grip_exclusion_metadata(self):
        return {'model':'conditional_reduced_ideal_grip','qualified_retention':False,
                'parts':['D02_pad_A','D02_pad_B'],
                'gripped_edges':sorted(self.grip_regions),
                'body_regions_mm':{str(e):[lo.tolist(),hi.tolist()]for e,(lo,hi)in self.grip_regions.items()},
                'scope':'Only declared fixed material edges against their bounded own-pad regions. Pin, jaws, spacers, fasteners, free edges and other solids remain active.'}

    def set_pose(self,center,angles):
        self.center=np.array(center);self.angles=np.array(angles);self.R,self.dR=rotation(angles,self.spec['angular_scale_mm']);middle=(self.local_lo+self.local_hi)/2;half=(self.local_hi-self.local_lo)/2;mid=self.center+self.R@middle;span=abs(self.R)@half;self.lo=mid-span;self.hi=mid+span

    def distance_for_edges(self,p,edge_ids):
        local=(np.asarray(p,dtype=float)-self.center)@self.R
        edges=None if edge_ids is None else np.broadcast_to(np.asarray(edge_ids),(len(local),))
        d,g=self.rigid.distance(local);pd,pg=self.pads.distance(local)
        if edges is not None:
            for edge,pad in self.reduced_pads.items():
                ids=np.flatnonzero(edges==edge)
                if not len(ids):continue
                pd[ids],pg[ids]=pad.distance(local[ids])
        use=pd<d;d[use]=pd[use];g[use]=pg[use]
        cylinders=list(self.spacers)
        pin=self.spec.get('return_pin')
        if pin:cylinders.append((np.asarray(pin['center_body_mm']),pin['length_mm'],-2e9,pin['diameter_mm']/2))
        for origin,length,inner,outer in cylinders:
            v,n=annular_cylinder(local,np.array([0.,1.,0.]),origin,-length/2,length/2,inner,outer)
            use=v<d;d[use]=v[use];g[use]=n[use]
        return d,g@self.R.T

    def distance(self,p):
        return self.distance_for_edges(p,None)

    def edge_contact_terms(self,q,rest,counts,radius):
        edge,t,weight,p=edge_samples(q,rest,counts,self.lo,self.hi,radius)
        if len(edge):
            d,g=self.distance_for_edges(p,edge);yield edge,t,weight,d,g
