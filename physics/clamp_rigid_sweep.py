"""Continuous native-clamp versus installed hardware clearance certificate.

Separate from yarn contact: native rigid surfaces keep the declared mechanical
reserve. Midpoint native distance minus rigid-point travel bounds the interval.
Intentional clamp internal mates are omitted by assembly identity only.
"""
import numpy as np
from physics.feed_native import hardware
from cad.transfer import installation as install
from physics.feeder_domain import feeder_potential
from physics.native_remainder import carrier_part


def clamp_part(name):
    return name.startswith(('D01_', 'D02_', 'D03_', 'D04_',
                            'HW_M3x16_cloth_', 'HW_M3nut_cloth_'))


class RigidClampSweepGuard:
    def __init__(self, model, state, guide, clearance=.3, max_depth=10):
        self.model=model;self.clearance=float(clearance);self.max_depth=max_depth
        if not np.isfinite(self.clearance)or self.clearance<0 or not np.isfinite(model.angle_scale)or model.angle_scale<=0:
            raise ValueError('Finite nonnegative clearance and positive angular scale required')
        ps,tp=hardware();q,c,a,z=model.unpack(model.x0)
        scene=install.installed(ps,tp,*state[:3],guide,reset=state[3],
            carrier_z=z,feed_mode=model.mode.lower(),clamp_pose=(np.zeros(3),np.zeros(3)))
        own=[shape for name,shape in scene.items()if clamp_part(name)]
        if not own:raise ValueError('No native clamp solids')
        self.local=install.base.cq.Compound.makeCompound(own)
        b=self.local.BoundingBox();self.radius=float(np.linalg.norm(np.maximum(
            abs(np.array([b.xmin,b.ymin,b.zmin])),abs(np.array([b.xmax,b.ymax,b.zmax])))))
        self.z0=z;self.cz0=feeder_potential(z,model.feeder,model.mode)[2]
        self.parts=[]
        for name,shape in scene.items():
            if clamp_part(name):continue
            box=shape.BoundingBox();kind='carrier'if carrier_part(name)else'counter'if name=='P18_weight_cup'else'fixed'
            self.parts.append((name,shape,np.array([box.xmin,box.ymin,box.zmin]),
                               np.array([box.xmax,box.ymax,box.zmax]),kind))
        if not self.parts or not np.isfinite(self.radius)or self.radius<=0:raise ValueError('Invalid native clearance scene')
        self.last=None

    def pose(self,c,angles):
        yaw,pitch,roll=np.asarray(angles)*180/np.pi/self.model.angle_scale
        return self.local.rotate((0,0,0),(1,0,0),float(roll)).rotate(
            (0,0,0),(0,1,0),float(-pitch)).rotate((0,0,0),(0,0,1),float(yaw)).translate(tuple(c))

    def __call__(self,a,b,deadline_check=lambda:None):
        if not np.all(np.isfinite(a))or not np.all(np.isfinite(b)):raise ValueError('Nonfinite rigid trajectory')
        delta=np.asarray(b)-a;m=self.model;n=m.interior
        speed=np.linalg.norm(delta[n:n+3])+self.radius*sum(abs(delta[n+3:n+6]))/m.angle_scale
        if not np.isfinite(speed):raise ValueError('Nonfinite rigid speed')
        leaves=[(0.,1.,0)];queries=0;minimum=float('inf');worst=None
        while leaves:
            deadline_check();lo,hi,depth=leaves.pop();t=(lo+hi)/2;half=(hi-lo)/2
            q,c,angles,z=m.unpack(a+t*delta);shape=self.pose(c,angles);bb=shape.BoundingBox()
            low=np.array([bb.xmin,bb.ymin,bb.zmin]);high=np.array([bb.xmax,bb.ymax,bb.zmax])
            zl=float(a[-1]+lo*delta[-1]);zh=float(a[-1]+hi*delta[-1]);cz=feeder_potential(z,m.feeder,m.mode)[2]
            czl=feeder_potential(zl,m.feeder,m.mode)[2];czh=feeder_potential(zh,m.feeder,m.mode)[2]
            bound=float('inf');actual=float('inf');pair=None
            for name,other,olow,ohigh,kind in self.parts:
                shift=z-self.z0 if kind=='carrier'else cz-self.cz0 if kind=='counter'else 0.
                motion=speed*half+(abs(delta[-1])*half if kind=='carrier'else max(abs(czl-cz),abs(czh-cz))if kind=='counter'else 0.)
                offset=np.array([0.,0.,shift]);distance=float(np.linalg.norm(np.maximum(np.maximum(olow+offset-high,low-ohigh-offset),0.)))
                if distance-motion<self.clearance:
                    deadline_check();distance=float(shape.distance(other.translate(tuple(offset))));queries+=1
                if not np.isfinite(distance+motion):raise ValueError('Nonfinite native distance or motion')
                if distance<actual:actual=distance
                if distance-motion<bound:bound=distance-motion;pair=name
            if bound>=self.clearance:
                if bound<minimum:minimum=bound;worst=pair
                continue
            if actual<self.clearance or depth>=self.max_depth:
                self.last={'certified':False,'fraction':t,'depth':depth,'minimum_bound_mm':bound,'worst_part':pair,'required_clearance_mm':self.clearance,'queries':queries};return False
            leaves.extend([(lo,t,depth+1),(t,hi,depth+1)])
        self.last={'certified':True,'minimum_bound_mm':minimum,'worst_part':worst,'required_clearance_mm':self.clearance,'queries':queries,'scope':'Native clamp vs all external installed hardware; intentional internal mates excluded. Nominal .3mm reserve; no material or friction qualification.'};return True
