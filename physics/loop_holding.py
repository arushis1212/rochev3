"""Coupled active yarn, hanging rigid clamp and registered textile load paths.
The six tension members are an explicit fabric surrogate, not calibrated fabric.
"""
import numpy as np
from scipy.optimize import minimize
from physics.banded_newton import minimize_banded
from physics.bordered_newton import minimize_bordered
from types import SimpleNamespace
from physics.roche_contact3d import HookContact,extrusion_distance,contact_energy3d,self_contact,self_pairs
from physics.roche_rod import energy_gradient


def head_frame(tip,angle=30.,roll=20.):
    a=np.deg2rad(angle);r=np.deg2rad(roll)
    u=np.array([0.,np.cos(a),-np.sin(a)]);v=np.array([0.,np.sin(a),np.cos(a)]);w=np.array([1.,0.,0.])
    return np.array(tip)-5*u,np.column_stack([u,np.cos(r)*v+np.sin(r)*w,-np.sin(r)*v+np.cos(r)*w])


class HoldingContact:
    def __init__(self,profiles,tip,gate,front_inner=None):
        self.profiles=profiles;self.origin,self.frame=head_frame(tip);self.hook=HookContact(profiles,gate);self.front_inner=front_inner
    def components(self,p):
        parts=[(d,g@self.frame.T) for d,g in self.hook.components((p-self.origin)@self.frame)]
        plate=self.profiles['B06_knockover']
        shifts=[0.] if self.front_inner is None else [0.,self.front_inner-plate['extrusion_bounds_mm'][1]]
        for shift in shifts:
            x=p.copy();x[:,1]-=shift;parts.append(extrusion_distance(x,plate))
        return parts
    def distance(self,p):
        parts=self.components(p);d,g=parts[0]
        for pd,pg in parts[1:]:
            use=pd<d;d[use]=pd[use];g[use]=pg[use]
        return d,g


def bar_direction(scaled_angles,scale=44.):
    a,b=scaled_angles/scale;ca,sa,cb,sb=np.cos(a),np.sin(a),np.cos(b),np.sin(b)
    return np.array([cb*ca,cb*sa,sb]),np.array([-cb*sa,cb*ca,0.])/scale,np.array([-sb*ca,-sb*sa,cb])/scale


def tension_members(points,anchors,rest,EA):
    e=points-anchors;l=np.linalg.norm(e,axis=1);delta=np.maximum(l-rest,0.)
    return float(np.sum(EA*delta*delta/(2*rest))),(EA*delta/rest/l)[:,None]*e


def initial_state(cfg,tip):
    center=np.array(cfg['clamp_initial_center_xyz_mm']);offsets=np.array(cfg['active_attachment_offsets_x_mm']);ends=center+offsets[:,None]*np.array([1.,0.,0.])
    origin,M=head_frame(tip);left=origin+M@np.array([0.,0.,-3.]);right=origin+M@np.array([0.,0.,3.])
    # Cluster leg nodes near the tool. This is a prescribed starting strand,
    # not a claim the prior stitch produced it without intervention.
    t=1-(1-np.linspace(0,1,cfg['leg_segments']+1))**2
    leg=ends[0]+t[:,None]*(left-ends[0]);bridge=np.linspace(left,right,cfg['bridge_segments']+1)[1:]
    other=(ends[1]+t[:,None]*(right-ends[1]))[::-1][1:]
    q=np.vstack([leg,bridge,other]);rest=np.linalg.norm(np.diff(q,axis=0),axis=1)
    return q,rest,center,np.zeros(2)


def contact_counts(rest,cfg):
    minimum=cfg['contact_samples_per_edge']
    spacing=cfg.get('contact_reference_spacing_mm')
    return minimum if spacing is None else np.maximum(minimum,np.ceil(rest/spacing).astype(int))


def rod_gravity(q,rest,linear_density_g_per_m):
    if not np.isfinite(linear_density_g_per_m) or linear_density_g_per_m<0:raise ValueError('Nonnegative finite yarn linear density required')
    edge_weight=np.asarray(rest)*linear_density_g_per_m*.00980665/1000
    nodal=np.zeros(len(q));nodal[:-1]+=edge_weight/2;nodal[1:]+=edge_weight/2
    gradient=np.zeros_like(q);gradient[:,2]=nodal
    return float(nodal@q[:,2]),gradient


def objective(q,rest,center,angles,cfg,obstacle):
    n,da,db=bar_direction(angles);offsets=np.array(cfg['active_attachment_offsets_x_mm'])
    p=q.copy();p[[0,-1]]=center+offsets[:,None]*n
    E,g=energy_gradient(p,rest,cfg['EA_N'],cfg['B_Nmm2'])
    G,gg=rod_gravity(p,rest,cfg.get('yarn_linear_density_g_per_m',0.));E+=G;g+=gg
    C,h=contact_energy3d(p,rest,cfg['yarn_radius_mm'],cfg['penalty_N_per_mm2'],obstacle,contact_counts(rest,cfg))
    S,j,_=self_contact(p,rest,cfg['yarn_radius_mm'],cfg['penalty_N_per_mm2'],self_pairs(rest,cfg['yarn_radius_mm']));g+=h+j
    xx=np.array(cfg['neighbor_support_x_mm']);yz=cfg['support_contact_yz_mm'];anchors=np.column_stack([xx,np.full(len(xx),yz[0]),np.full(len(xx),yz[1])]);po=xx-cfg['clamp_initial_center_xyz_mm'][0]
    baseline=np.array(cfg['clamp_initial_center_xyz_mm'])+po[:,None]*np.array([1.,0.,0.]);lengths=np.linalg.norm(baseline-anchors,axis=1)
    bottom=center+po[:,None]*n;P,pg=tension_members(bottom,anchors,lengths,cfg['EA_N'])
    weight=cfg['clamp_mass_g']*.00980665
    cg=g[0]+g[-1]+pg.sum(axis=0)+[0.,0.,weight]
    moment_vector=np.sum(offsets[:,None]*g[[0,-1]],axis=0)+np.sum(po[:,None]*pg,axis=0)
    ag=np.array([moment_vector@da,moment_vector@db]);torque=np.cross(n,moment_vector)
    return E+C+S+P+weight*center[2],g,cg,ag,{'clamp_force_residual_xyz_N':cg.tolist(),'clamp_torque_residual_Nmm':torque.tolist(),'neighbor_tensions_N':np.linalg.norm(pg,axis=1).tolist(),'clamp_z_mm':float(center[2])}


def valid_inverse_hessian(matrix,size):
    """A positive search metric changes convergence, never the energy or forces."""
    if matrix is None:return None
    H=np.asarray(matrix,dtype=float)
    if H.shape!=(size,size) or not np.all(np.isfinite(H)):return None
    H=(H+H.T)/2
    try:np.linalg.cholesky(H)
    except np.linalg.LinAlgError:return None
    return H


def solve_holding(q,rest,center,angles,cfg,obstacle,optimizer_memory=None,checkpoint=None):
    count=q[1:-1].size
    def unpack(x):
        c=x[count:count+3];a=x[count+3:];n,_,_=bar_direction(a);p=q.copy();p[1:-1]=x[:count].reshape(-1,3);p[[0,-1]]=c+np.array(cfg['active_attachment_offsets_x_mm'])[:,None]*n
        return p,c,a
    def evaluate(x):
        p,c,a=unpack(x);E,g,cg,ag,_=objective(p,rest,c,a,cfg,obstacle)
        return E,np.concatenate([g[1:-1].ravel(),cg,ag])
    x=np.concatenate([q[1:-1].ravel(),center,angles])
    pairs=self_pairs(rest,cfg['yarn_radius_mm'])
    def local_safe(y):
        p,_,_=unpack(y)
        return self_contact(p,rest,cfg['yarn_radius_mm'],cfg['penalty_N_per_mm2'],pairs)[2]>4e-6
    options={'gtol':1e-8,'maxiter':cfg.get('BFGS_max_iterations',1500)}
    H=valid_inverse_hessian(optimizer_memory.get('inverse_hessian') if optimizer_memory is not None else None,len(x))
    if H is not None:options['hess_inv0']=H
    if cfg.get('solver_method')=='bordered_newton':
        def save(y,diagnostic):
            if checkpoint is not None:checkpoint(*unpack(y),diagnostic)
        solution,diagnostic=minimize_bordered(evaluate,x,count,local_safe,maxiter=cfg.get('bordered_max_iterations',200),max_step=cfg.get('bordered_max_step_mm',.25),step=cfg.get('bordered_difference_step_mm',1e-6),callback=save)
        opt=SimpleNamespace(x=solution,nit=diagnostic['iterations'],message=diagnostic['message'])
    else:
        diagnostic=None
        opt=minimize(evaluate,x,method='BFGS',jac=True,options=options)
    if optimizer_memory is not None:
        saved=valid_inverse_hessian(getattr(opt,'hess_inv',None),len(x))
        optimizer_memory['inverse_hessian']=None if saved is None else saved.tolist()
    solution=opt.x;refinement=None
    if cfg.get('solver_method')!='bordered_newton' and cfg.get('newton_refinement_iterations',0) and np.max(abs(evaluate(solution)[1]))>1e-8:
        if cfg.get('newton_polish_method')=='bordered':
            solution,refinement=minimize_bordered(evaluate,solution,count,local_safe,gtol=1e-8,maxiter=cfg['newton_refinement_iterations'],step=1e-6)
        else:solution,refinement=minimize_banded(evaluate,solution,bandwidth=len(solution)-1,gtol=1e-8,maxiter=cfg['newton_refinement_iterations'],step=1e-6)
    p,c,a=unpack(solution);E,g,cg,ag,info=objective(p,rest,c,a,cfg,obstacle)
    residual=max(float(np.max(abs(g[1:-1]))),float(np.max(abs(cg))),float(np.linalg.norm(info['clamp_torque_residual_Nmm'])/44))
    lo,hi=cfg['clamp_z_safety_bound_mm'];inside=lo<c[2]<hi
    info.update(optimizer_success=bool(residual<=1e-7 and inside),force_residual_N=residual,iterations=int(opt.nit),message=str(opt.message),clamp_center_xyz_mm=c.tolist(),bar_angles_scaled_mm=a.tolist(),energy_Nmm=float(E),domain_guard_clear=bool(inside),centerline_xyz_mm=p.tolist())
    if refinement is not None:info['newton_refinement']=refinement
    if diagnostic is not None:info['bordered_newton']=diagnostic
    return p,c,a,info
