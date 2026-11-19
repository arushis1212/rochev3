"""Secant initial guess only; accepted material states remain authoritative."""
import numpy as np

def predict(q,center,angles,state,target,previous,max_node_motion=1.):
    if previous is None:return q,center,angles
    old=np.asarray(previous['state']);state=np.asarray(state);target=np.asarray(target)
    delta=state-old;next_delta=target-state;active=np.flatnonzero(abs(delta)>1e-12)
    # Predict only one continuing axis, not a phase switch or motion reversal.
    if len(active)!=1:return q,center,angles
    axis=active[0]
    if np.any(abs(np.delete(next_delta,axis))>1e-12) or delta[axis]*next_delta[axis]<=0:return q,center,angles
    ratio=next_delta[axis]/delta[axis];dq=np.asarray(q)-np.asarray(previous['q']);dc=np.asarray(center)-np.asarray(previous['center']);da=np.asarray(angles)-np.asarray(previous['angles'])
    if dq.shape!=np.asarray(q).shape or not all(np.isfinite(x).all()for x in [dq,dc,da]):raise ValueError('Invalid predictor history')
    scale=min(1.,max_node_motion/max(1e-12,float(np.max(np.linalg.norm(ratio*dq,axis=1)))))
    return q+scale*ratio*dq,center+scale*ratio*dc,angles+scale*ratio*da
