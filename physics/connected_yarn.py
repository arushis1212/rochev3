"""Continuous material route across a cloth clamp into a captured working strand.
One old bight, not the two old loops of a complete single-crochet stitch.
The clamp is a material boundary for bending, but the node and material ID are shared.
"""
import numpy as np
from scipy.optimize import minimize
from physics.loop_holding import bar_direction,rod_gravity,tension_members,contact_counts,valid_inverse_hessian
from physics.roche_rod import energy_gradient
from physics.roche_contact3d import contact_energy3d,self_contact,self_pairs
from physics.bordered_newton import minimize_bordered

def connected_objective(q,rest,split,center,angles,guide,cfg,obstacle):
    n,da,db=bar_direction(angles);offsets=np.asarray(cfg['active_attachment_offsets_x_mm'])
    p=q.copy();p[[0,split]]=center+offsets[:,None]*n;p[-1]=guide
    E,g0=energy_gradient(p[:split+1],rest[:split],cfg['EA_N'],cfg['B_Nmm2']);W,g1=energy_gradient(p[split:],rest[split:],cfg['EA_N'],cfg['B_Nmm2']);g=np.zeros_like(p);g[:split+1]+=g0;g[split:]+=g1
    G,gg=rod_gravity(p,rest,cfg.get('yarn_linear_density_g_per_m',0));g+=gg
    C,cg=contact_energy3d(p,rest,cfg['yarn_radius_mm'],cfg['penalty_N_per_mm2'],obstacle,contact_counts(rest,cfg));S,sg,gap=self_contact(p,rest,cfg['yarn_radius_mm'],cfg['penalty_N_per_mm2'],self_pairs(rest,cfg['yarn_radius_mm']));g+=cg+sg
    xx=np.asarray(cfg['neighbor_support_x_mm']);yz=cfg['support_contact_yz_mm'];anchors=np.column_stack([xx,np.full(len(xx),yz[0]),np.full(len(xx),yz[1])]);po=xx-cfg['clamp_initial_center_xyz_mm'][0];baseline=np.asarray(cfg['clamp_initial_center_xyz_mm'])+po[:,None]*[1,0,0]
    P,pg=tension_members(center+po[:,None]*n,anchors,np.linalg.norm(baseline-anchors,axis=1),cfg['EA_N']);weight=cfg['clamp_mass_g']*.00980665
    force=g[0]+g[split]+pg.sum(axis=0)+[0,0,weight];moment=np.sum(offsets[:,None]*g[[0,split]],axis=0)+np.sum(po[:,None]*pg,axis=0);ag=np.array([moment@da,moment@db]);torque=np.cross(n,moment)
    return E+W+G+C+S+P+weight*center[2],g,force,ag,{'clamp_torque_residual_Nmm':torque.tolist(),'guide_reaction_N':g[-1].tolist(),'self_contact_gap_mm':gap}

def solve_connected(q,rest,split,center,angles,guide,cfg,obstacle,callback=None,memory=None):
    free=np.array([i for i in range(len(q)) if i not in [0,split,len(q)-1]]);m=3*len(free)
    def unpack(x):
        c=x[m:m+3];a=x[m+3:];p=q.copy();p[free]=x[:m].reshape(-1,3);p[[0,split]]=c+np.asarray(cfg['active_attachment_offsets_x_mm'])[:,None]*bar_direction(a)[0];p[-1]=guide;return p,c,a
    def fun(x):
        p,c,a=unpack(x);E,g,cg,ag,_=connected_objective(p,rest,split,c,a,guide,cfg,obstacle);return E,np.concatenate([g[free].ravel(),cg,ag])
    x=np.concatenate([q[free].ravel(),center,angles]);iterations=[]
    def save(y):
        if callback:callback(*unpack(y))
    options={'gtol':1e-8,'maxiter':cfg.get('connected_iterations',600)}
    H=valid_inverse_hessian(memory.get('inverse_hessian') if memory is not None else None,len(x))
    if H is not None:options['hess_inv0']=H
    if cfg.get('connected_newton_first'):
        from scipy.optimize import OptimizeResult
        opt=OptimizeResult(x=x,nit=0,message='Newton-first contact branch',hess_inv=np.eye(len(x)))
    else:
        opt=minimize(fun,x,method='BFGS',jac=True,callback=save,options=options)
    if memory is not None:
        H=valid_inverse_hessian(opt.hess_inv,len(x));memory['inverse_hessian']=None if H is None else H.tolist()
    solution=opt.x;refinement=None
    if np.max(abs(fun(solution)[1]))>1e-8:
        pairs=self_pairs(rest,cfg['yarn_radius_mm'])
        def safe(x):return self_contact(unpack(x)[0],rest,cfg['yarn_radius_mm'],cfg['penalty_N_per_mm2'],pairs)[2]>4e-6
        solution,refinement=minimize_bordered(fun,solution,m,safe,maxiter=cfg.get('connected_newton_iterations',200),max_step=.5,step=cfg.get('connected_difference_step_mm',1e-6),callback=lambda x,d:save(x),spectral=cfg.get('connected_spectral_newton',False))
    p,c,a=unpack(solution);E,g,cg,ag,info=connected_objective(p,rest,split,c,a,guide,cfg,obstacle);res=max(float(np.max(abs(g[free]))),float(np.max(abs(cg))),float(np.linalg.norm(info['clamp_torque_residual_Nmm'])/44));lo,hi=cfg['clamp_z_safety_bound_mm']
    if refinement is not None:info['newton_refinement']=refinement
    info.update(force_residual_N=res,optimizer_success=bool(res<=1e-7 and lo<c[2]<hi),iterations=int(opt.nit),message=str(opt.message),energy_Nmm=float(E),maximum_strain=float(np.max(np.linalg.norm(np.diff(p,axis=0),axis=1)/rest-1)),centerline_xyz_mm=p.tolist(),clamp_center_xyz_mm=c.tolist(),bar_angles_scaled_mm=a.tolist());return p,c,a,info
