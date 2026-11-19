"""Conservative line-search bounds for the registered frictionless feed model.

Signed distances are 1-Lipschitz. A point with speed bound v can lose at most
v*dt in clearance; two segments can lose at most 2*v*dt in separation.
The tolerance is the existing numerical penetration allowance, not clearance
for manufacturing. This is not an IPC barrier/dynamics implementation.
"""
import numpy as np
from physics.roche_contact3d import self_contact,closest_segments


def adaptive_solid_bound(q, obstacle, spacing=.004, ceiling=.32):
    """Lower bound for every polyline segment; adapt only near surfaces.

    Midpoint SDF minus half segment length bounds the entire segment. Segments
    already above ceiling need no subdivision. Return a conservative bound,
    even at the spatial recursion limit; unresolved paths are never accepted.
    """
    q=np.asarray(q,dtype=float);a=q[:-1].copy();b=q[1:].copy()
    ceilings=np.broadcast_to(np.asarray(ceiling,dtype=float),(len(a),)).copy();bounds=ceilings.copy();ids=np.arange(len(a));sample=float('inf');evaluations=0
    for _ in range(24):
        if len(a)==0:break
        length=np.linalg.norm(b-a,axis=1);mid=(a+b)/2
        if hasattr(obstacle,'clipped_distance'):
            cutoff=ceilings[ids]+length/2+1e-10
            d=(obstacle.clipped_distance(mid,cutoff,edge_ids=ids)
               if hasattr(obstacle,'distance_for_edges') else obstacle.clipped_distance(mid,cutoff))
        elif hasattr(obstacle,'distance_for_edges'):
            d=obstacle.distance_for_edges(mid,ids)[0]
        else:d=obstacle.distance(mid)[0]
        evaluations+=len(mid)
        if not np.all(np.isfinite(d)):raise ValueError('Nonfinite contact distance')
        sample=min(sample,float(np.min(d)));lower=d-length/2
        done=(lower>=ceilings[ids])|(length<=spacing)
        if np.any(done):np.minimum.at(bounds,ids[done],lower[done])
        keep=~done;aa=a[keep];bb=b[keep];mm=mid[keep]
        a=np.concatenate([aa,mm]);b=np.concatenate([mm,bb]);ids=np.concatenate([ids[keep],ids[keep]])
    else:
        # A residual interval is unknown, never collision-free by assumption.
        return {'lower':-float('inf'),'edge_lower':np.full(len(bounds),-float('inf')),'sample':sample,'queries':evaluations}
    return {'lower':float(np.min(bounds)),'edge_lower':bounds,'sample':sample,'queries':evaluations}


def local_self_swept_bound(q, pairs, radius, node_speed, half_interval, ceiling=.02):
    """All registered pairs; box culling excludes only pairs already above cutoff."""
    i,j=pairs
    if len(i)==0:return float('inf'),float('inf')
    speed=np.broadcast_to(np.asarray(node_speed,dtype=float),(len(q),))
    edge_speed=np.maximum(speed[:-1],speed[1:]);motion=(edge_speed[i]+edge_speed[j])*half_interval
    lo=np.minimum(q[:-1],q[1:]);hi=np.maximum(q[:-1],q[1:])
    box=np.linalg.norm(np.maximum(np.maximum(lo[i]-hi[j],lo[j]-hi[i]),0.),axis=1)
    lower=box-2*radius-motion;keep=lower<ceiling
    if not np.any(keep):return ceiling,ceiling
    ii,jj=i[keep],j[keep]
    distance=closest_segments(q[ii],q[ii+1],q[jj],q[jj+1])[0]-2*radius
    return min(ceiling,float(np.min(distance-motion[keep]))),min(ceiling,float(np.min(distance)))


def certify_configuration_path(configuration, obstacle_at, speed, rigid_speed,
                               rest, radius, pairs, allowance=.01,
                               max_depth=7, spacing=.004):
    """Certify the actual configuration(t), with known speeds on t in[0,1]."""
    speed=np.asarray(speed,dtype=float)
    if np.any(speed<0) or min(rigid_speed,allowance)<0 or not np.all(np.isfinite(speed))or not np.isfinite(rigid_speed+allowance):
        raise ValueError('Finite nonnegative motion bounds required')
    maximum_speed=float(np.max(speed));edge_speed=np.maximum(speed[:-1],speed[1:])if speed.ndim else speed
    leaves=[(0.,1.,0)];solid=float('inf');strand=float('inf');count=0;queries=0
    while leaves:
        lo,hi,depth=leaves.pop();t=(lo+hi)/2;half=(hi-lo)/2;q=configuration(t)
        gap=adaptive_solid_bound(q,obstacle_at(t),spacing,ceiling=radius+.02+(edge_speed+rigid_speed)*half)
        yb,sg=local_self_swept_bound(q,pairs,radius,speed,half);count+=1;queries+=gap['queries']
        sb=float(np.min(gap['edge_lower']-radius-(edge_speed+rigid_speed)*half))
        if sb>=-allowance and yb>=-allowance:
            solid=min(solid,sb);strand=min(strand,yb);continue
        if gap['sample']-radius < -allowance or sg < -allowance or depth>=max_depth:
            return {'certified':False,'reason':'contact_or_unresolved_interval',
                    'fraction':t,'solid_bound_mm':float(sb),'self_bound_mm':float(yb),
                    'samples':count,'distance_queries':queries,'depth':depth}
        leaves.extend([(lo,t,depth+1),(t,hi,depth+1)])
    return {'certified':True,'solid_bound_mm':float(solid),'self_bound_mm':float(strand),
            'samples':count,'distance_queries':queries,'speed_bound_mm':maximum_speed,
            'rigid_speed_bound_mm':float(rigid_speed),'allowance_mm':allowance,
            'scope':'Swept registered polyline/tube with numerical penetration allowance; fixed pose, rotating clamp and translating feeder.'}


class FeedStepGuard:
    def __init__(self,model,allowance=.01,max_depth=7,spacing=.004):
        self.model=model;self.allowance=allowance;self.max_depth=max_depth;self.spacing=spacing
        self.last=None;self.accepted=0;self.rejected=0
    def __call__(self,a,b):
        m=self.model;delta=np.asarray(b)-np.asarray(a);n=m.interior
        speeds=np.zeros(len(m.q));speeds[m.free]=np.linalg.norm(delta[:n].reshape(-1,3),axis=1)
        # |dn/da|,|dn/db| <= 1/44 for the actual spherical bar direction.
        clamp=float(np.linalg.norm(delta[n:n+3]))+abs(np.asarray(m.cfg['active_attachment_offsets_x_mm']))*float(abs(delta[n+3:n+5]).sum())/44
        rigid=abs(float(delta[-1]))
        if hasattr(m,'step_speed_bounds'):clamp,rigid=m.step_speed_bounds(delta)
        speeds[getattr(m,'fixed_indices',[0,m.split])]=clamp
        old_z=m.obstacle.moving.center[2]
        def obstacle(t):
            if hasattr(m,'set_obstacle_pose'):m.set_obstacle_pose(a+t*delta)
            else:m.obstacle.moving.center[2]=float(a[-1]+t*delta[-1])
            return m.obstacle
        try:
            self.last=certify_configuration_path(lambda t:m.unpack(a+t*delta)[0],obstacle,
                speeds,rigid,m.rest,m.cfg['yarn_radius_mm'],m.pairs,self.allowance,self.max_depth,self.spacing)
        finally:
            if hasattr(m,'set_obstacle_pose'):m.set_obstacle_pose(a)
            else:m.obstacle.moving.center[2]=old_z
        if self.last['certified']:self.accepted+=1
        else:self.rejected+=1
        return self.last['certified']
