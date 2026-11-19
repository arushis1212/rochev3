"""Finite active-face solution of a small strictly convex box search model.

This is a numerical proposal only. Physical objectives and guards remain separate.
"""
from itertools import product
import numpy as np


def minimize_spd_box(matrix,gradient,limit):
    H=np.array(matrix,dtype=float,copy=True);g=np.array(gradient,dtype=float,copy=True)
    if (g.ndim!=1 or not 1<=len(g)<=7 or H.shape!=(len(g),len(g))
            or not np.isfinite(H).all()or not np.isfinite(g).all()
            or not np.array_equal(H,H.T)or isinstance(limit,(bool,np.bool_))
            or not np.isscalar(limit)or not np.isfinite(limit)or limit<=0):
        raise ValueError('Finite exactly symmetric SPD box of dimension one through seven required')
    try:L=np.linalg.cholesky(H)
    except np.linalg.LinAlgError as error:raise ValueError('Positive-definite search metric required')from error
    if not np.isfinite(L).all():raise ValueError('Nonfinite positive-definite factor')
    best=None;bestvalue=np.inf;feasible=0;faces=0
    for status in product((-1,0,1),repeat=len(g)):
        faces+=1;s=np.array(status);free=np.flatnonzero(s==0);active=np.flatnonzero(s!=0);x=limit*s.astype(float)
        with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
            if len(free):x[free]=np.linalg.solve(H[np.ix_(free,free)],-g[free]-H[np.ix_(free,active)]@x[active])
            if not np.isfinite(x).all():raise ValueError('Nonfinite active-face solution')
            if np.any(abs(x)>limit):continue
            value=float(g@x+.5*x@H@x)
        if not np.isfinite(value):raise ValueError('Nonfinite box objective')
        feasible+=1
        if value<bestvalue:bestvalue=value;best=x.copy();beststatus=s.copy()
    if best is None:raise ValueError('No finite feasible box candidate')
    with np.errstate(over='ignore',invalid='ignore'):
        gradient_at_best=g+H@best
        residual=np.where(beststatus==0,abs(gradient_at_best),np.where(beststatus<0,np.maximum(-gradient_at_best,0),np.maximum(gradient_at_best,0)))
        scale=max(1.,float(abs(g).max()),float(np.linalg.norm(H,ord=np.inf)*limit))
        error=float(residual.max());scaled=error/scale
    if not np.isfinite([scale,error,scaled]).all()or not np.isfinite(gradient_at_best).all():raise ValueError('Nonfinite box KKT arithmetic')
    if scaled>1e-10:raise ValueError('Box candidate failed scaled KKT residual')
    return best,dict(scope='Exact finite active-face candidate set for the authored SPD numerical quadratic; not physical equilibrium',dimension=len(g),faces_evaluated=faces,maximum_faces=3**len(g),feasible_faces=feasible,selected_status=beststatus.tolist(),objective_value=bestvalue,gradient_at_solution=gradient_at_best.tolist(),kkt_residual_N=error,kkt_scale_N=scale,kkt_scaled_residual=scaled,kkt_scaled_tolerance=1e-10,coordinate_bound_mm=float(limit))
