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

class ClampContact(BoxUnion):
    def __init__(self,spec,center,angles):
        self.spec=spec;g=spec['closed_face_gap_mm']/2;p=g+spec['pad_thickness_mm'];o=p+spec['jaw_thickness_mm'];h=spec['body_height_mm']/2;w=spec['body_width_mm']/2;wp=spec['pad_width_mm']/2
        boxes=[([-w,-o,-h],[w,-p,h]),([-wp,-p,-h],[wp,-g,h]),([-w,p,-h],[w,o,h]),([-wp,g,-h],[wp,p,h])]
        # Shaft/head/nut envelopes preserve all clamp hardware in contact checks.
        for x in spec['bolt_x_mm']:
            boxes.extend([([x-1.5,-o,-1.5],[x+1.5,16-o,1.5]),([x-2.84,-o-3,-2.84],[x+2.84,-o,2.84]),([x-3.2,o,-3.2],[x+3.2,o+2.4,3.2])])
        super().__init__(boxes);self.local_lo=self.lo.copy();self.local_hi=self.hi.copy();self.radius=float(np.max(np.linalg.norm(np.array([self.local_lo,self.local_hi]),axis=1)));self.set_pose(center,angles)
    def set_pose(self,center,angles):
        self.center=np.array(center);self.angles=np.array(angles);self.R,self.dR=rotation(angles,self.spec['angular_scale_mm']);middle=(self.local_lo+self.local_hi)/2;half=(self.local_hi-self.local_lo)/2;mid=self.center+self.R@middle;span=abs(self.R)@half;self.lo=mid-span;self.hi=mid+span
    def distance(self,p):
        local=(np.asarray(p)-self.center)@self.R;d,g=super().distance(local)
        pin=self.spec.get('return_pin')
        if pin:
            v,n=annular_cylinder(local,np.array([0.,1.,0.]),np.array(pin['center_body_mm']),-pin['length_mm']/2,pin['length_mm']/2,-1e9,pin['diameter_mm']/2);mask=v<d;d[mask]=v[mask];g[mask]=n[mask]
        return d,g@self.R.T
