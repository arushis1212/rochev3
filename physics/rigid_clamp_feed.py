"""Material-conserving feed with a six-degree-of-freedom hanging clamp.
The fixed gripping material coordinates are conditional on measured retention.
All rod/neighbor/contact virtual work is transmitted to the physical COM.
"""
import numpy as np
from physics.feed_equilibrium import FeedEquilibrium
from physics.rigid_clamp import rotation
from physics.fixture_contact import ClampContact,BoxUnion,bank_boxes
from physics.roche_rod import energy_gradient
from physics.loop_holding import rod_gravity,tension_members
from physics.roche_contact3d import contact_energy3d,self_contact
from physics.feeder_domain import feeder_potential

class RigidClampFeedEquilibrium(FeedEquilibrium):
    angle_count=3
    def __init__(self,q,rest,split,center,angles,z,cfg,obstacle,feeder,mode,fixture,fixed_section=None):
        self.fixed_section=fixed_section;self.fixture=fixture;self.clamp_spec=fixture['cloth_clamp'];height=self.clamp_spec['attachment_height_above_com_mm'];self.angle_scale=self.clamp_spec['angular_scale_mm']
        self.attach_body=np.column_stack([cfg['active_attachment_offsets_x_mm'],[0.,0.],[height,height]])
        xx=np.asarray(cfg['neighbor_support_x_mm']);self.neighbor_body=np.column_stack([xx-cfg['clamp_initial_center_xyz_mm'][0],np.zeros(len(xx)),np.full(len(xx),height)])
        yz=cfg['support_contact_yz_mm'];self.anchors=np.column_stack([xx,np.full(len(xx),yz[0]),np.full(len(xx),yz[1])]);baseline=np.array(cfg['clamp_initial_center_xyz_mm'])+np.column_stack([self.neighbor_body[:,0],np.zeros((len(xx),2))]);self.neighbor_rest=np.linalg.norm(baseline-self.anchors,axis=1)
        self.clamp=ClampContact(self.clamp_spec,center,angles);bed,cover=bank_boxes(fixture);obstacle.fixed.extend([BoxUnion(bed),BoxUnion(cover),self.clamp]);super().__init__(q,rest,split,center,angles,z,cfg,obstacle,feeder,mode)
        self.fixed_indices=np.array(fixed_section['indices']if fixed_section else [0,split],dtype=int);self.fixed_body=np.array(fixed_section['body_xyz_mm'])if fixed_section else self.attach_body
        if fixed_section and fixed_section.get('gripped_edges'):
            self.clamp.set_gripped_edges(fixed_section)
        if fixed_section:
            self.free=np.array([i for i in range(len(q))if i not in set(self.fixed_indices)and i!=len(q)-1]);self.interior=3*len(self.free);self.x0=self.pack(q,center,angles,z)
    def unpack(self,x):
        m=self.interior;q=self.q.copy();q[self.free]=x[:m].reshape(-1,3);c=x[m:m+3];a=x[m+3:m+6];z=x[-1];R,_=rotation(a,self.angle_scale);q[self.fixed_indices]=c+self.fixed_body@R.T;q[-1]=self.nip
        return q,c,a,z
    def set_obstacle_pose(self,x):
        m=self.interior;self.obstacle.moving.center[2]=x[-1];self.clamp.set_pose(x[m:m+3],x[m+3:m+6])
    def step_speed_bounds(self,delta):
        m=self.interior;dc=float(np.linalg.norm(delta[m:m+3]));angle=float(sum(abs(delta[m+3:m+6])))/self.angle_scale
        return dc+np.linalg.norm(self.fixed_body,axis=1)*angle,max(abs(float(delta[-1])),dc+self.clamp.radius*angle)
    def energy(self,x):
        q,c,a,z=self.unpack(x);self.set_obstacle_pose(x);R,dR=rotation(a,self.angle_scale);cfg=self.cfg;k=cfg['penalty_N_per_mm2'];rad=cfg['yarn_radius_mm'];split=self.split
        E,g0=energy_gradient(q[:split+1],self.rest[:split],cfg['EA_N'],cfg['B_Nmm2']);W,g1=energy_gradient(q[split:],self.rest[split:],cfg['EA_N'],cfg['B_Nmm2']);g=np.zeros_like(q);g[:split+1]+=g0;g[split:]+=g1
        if self.fixed_section:E,g=energy_gradient(q,self.rest,cfg['EA_N'],cfg['B_Nmm2']);W=0.
        G,gg=rod_gravity(q,self.rest,cfg.get('yarn_linear_density_g_per_m',0));C,cg=contact_energy3d(q,self.rest,rad,k,self.obstacle,self.counts);S,sg,gap=self_contact(q,self.rest,rad,k,self.pairs);g+=gg+cg+sg
        P,pg=tension_members(c+self.neighbor_body@R.T,self.anchors,self.neighbor_rest,cfg['EA_N']);weight=self.clamp_spec['mass_target_g']*.00980665
        _,reaction=contact_energy3d(q,self.rest,rad,k,self.clamp,self.counts)
        force=g[self.fixed_indices].sum(axis=0)+pg.sum(axis=0)+[0,0,weight]-reaction.sum(axis=0)
        localq=(q-c)@R
        com=np.array(self.clamp_spec.get('com_body_xyz_mm',[0.,0.,0.]));gravity=np.array([0.,0.,weight])
        ag=np.array([np.sum(g[self.fixed_indices]*(self.fixed_body@D.T))+np.sum(pg*(self.neighbor_body@D.T))-np.sum(reaction*(localq@D.T))+weight*(D@com)[2]for D in dR])
        torque=np.cross(self.fixed_body@R.T,g[self.fixed_indices]).sum(axis=0)+np.cross(self.neighbor_body@R.T,pg).sum(axis=0)-np.cross(q-c,reaction).sum(axis=0)+np.cross(R@com,gravity)
        V,dV,_=feeder_potential(z,self.feeder,self.mode);_,mg=contact_energy3d(q,self.rest,rad,k,self.obstacle.moving,self.counts)
        self.last_info={'clamp_torque_residual_Nmm':torque.tolist(),'guide_reaction_N':g[-1].tolist(),'self_contact_gap_mm':gap,'clamp_contact_reaction_N':(-reaction.sum(axis=0)).tolist(),'neighbor_tensions_N':np.linalg.norm(pg,axis=1).tolist()}
        self.last_info['grip_reaction_N']={str(i):g[i].tolist()for i in self.fixed_indices}
        if self.fixed_section and self.fixed_section.get('grip_material_intervals_mm'):
            material=np.r_[0.,np.cumsum(self.rest)];lands=[]
            for lo,hi in self.fixed_section['grip_material_intervals_mm']:
                ids=self.fixed_indices[(material[self.fixed_indices]>=lo-1e-9)&(material[self.fixed_indices]<=hi+1e-9)]
                on_yarn=g[ids].sum(axis=0);moment=np.cross(q[ids]-c,g[ids]).sum(axis=0)
                lands.append({'material_interval_mm':[lo,hi],'constraint_force_on_yarn_N':on_yarn.tolist(),'force_on_clamp_N':(-on_yarn).tolist(),'moment_on_clamp_about_datum_Nmm':(-moment).tolist(),'resultant_N':float(np.linalg.norm(on_yarn))})
            self.last_info['grip_land_reactions']=lands
        self.last_info['world_com_mm']=(c+R@com).tolist()
        return E+W+G+C+S+P+weight*(c+R@com)[2]+V,np.r_[g[self.free].ravel(),force,ag,dV-mg[:,2].sum()]
    def checkpoint(self,x,state):
        cp=super().checkpoint(x,state);cp.update(clamp_pose_model='geometric_datum_RzRyRx_v1',com_body_xyz_mm=self.clamp_spec.get('com_body_xyz_mm',[0.,0.,0.]),mass_reference_g=self.clamp_spec['mass_target_g'],scope='Six-DOF clamp datum, connected material and gravity feeder; numerical endpoint conditional on material properties and gripping retention.')
        cp['fixed_section']=self.fixed_section
        if self.fixed_section:cp['clamp_pose_model']='free_pin_wrap_geometric_datum_v1'if self.fixed_section.get('gripped_edges')else'legacy_fixed_arc_geometric_datum_v1'
        return cp
