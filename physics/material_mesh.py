"""Material-preserving nested refinement of a piecewise-linear yarn route."""
import numpy as np

def refine_material(q,rest,split,factor):
 q=np.asarray(q,dtype=float);rest=np.asarray(rest,dtype=float)
 if isinstance(factor,bool) or not isinstance(factor,(int,np.integer)) or factor<1:raise ValueError('factor must be a positive integer')
 if q.ndim!=2 or q.shape[1]!=3 or rest.shape!=(len(q)-1,)or not 0<split<len(q)-1 or np.any(rest<=0)or not np.isfinite(q).all()or not np.isfinite(rest).all():raise ValueError('invalid material chain')
 t=np.arange(factor)/factor
 new=(q[:-1,None,:]+t[None,:,None]*(q[1:]-q[:-1])[:,None,:]).reshape(-1,3)
 return np.vstack([new,q[-1]]),np.repeat(rest/factor,factor),split*factor
