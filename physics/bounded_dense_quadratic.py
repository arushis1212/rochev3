"""Bounded dense SPD search quadratic; never a physical equilibrium solver."""
import numpy as np
from scipy.optimize import lsq_linear


def minimize_spd_box_bvls(matrix, gradient, limit):
    """Minimize .5*d.T*H*d + g.T*d on [-limit,limit], dimension <=19.

    H=L L.T gives the equivalent least-squares matrix L.T and target
    -solve(L,g). Admission checks the ORIGINAL quadratic KKT conditions,
    independently of the least-squares optimizer's success flag.
    """
    H = np.array(matrix, dtype=float, copy=True)
    g = np.array(gradient, dtype=float, copy=True)
    if (g.ndim != 1 or not 1 <= len(g) <= 19
            or H.shape != (len(g), len(g))
            or not np.isfinite(H).all() or not np.isfinite(g).all()
            or not np.array_equal(H, H.T)
            or isinstance(limit, (bool, np.bool_)) or not np.isscalar(limit)
            or not np.isfinite(limit) or limit <= 0):
        raise ValueError('Finite exactly symmetric dimension-one-through-19 box required')
    try:
        L = np.linalg.cholesky(H)
    except np.linalg.LinAlgError as error:
        raise ValueError('Positive-definite numerical quadratic required') from error
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        target = -np.linalg.solve(L, g)
        scale = max(1., float(abs(g).max()), float(np.linalg.norm(H, np.inf)*limit))
        condition = float(np.linalg.cond(H))
    if not np.isfinite(L).all() or not np.isfinite(target).all() or not np.isfinite([scale, condition]).all():
        raise ValueError('Nonfinite factor, target or original-QP scale')
    result = lsq_linear(L.T, target, bounds=(-limit, limit), method='bvls',
                        tol=1e-12, max_iter=20*len(g), verbose=0)
    d = np.array(result.x, dtype=float, copy=True)
    active = np.asarray(result.active_mask)
    if (d.shape != g.shape or active.shape != g.shape or not np.isfinite(d).all()
            or not np.isin(active, [-1, 0, 1]).all()):
        raise ValueError('Nonfinite or malformed bounded least-squares result')
    # Only roundoff-sized active-bound representation differences are snapped.
    # KKT signs below are then taken at the actual exact feasible coordinates.
    reserve = 32*np.finfo(float).eps*max(1., float(limit))
    for j in np.flatnonzero(active):
        bound = float(active[j])*limit
        if abs(d[j]-bound) > reserve:
            raise ValueError('Reported active bound differs from the actual coordinate')
        d[j] = bound
    if np.any(abs(d) > limit):
        raise ValueError('Infeasible bounded least-squares proposal')
    with np.errstate(over='ignore', invalid='ignore'):
        qgrad = H@d+g
        residual = np.where(d == -limit, np.maximum(-qgrad, 0),
                    np.where(d == limit, np.maximum(qgrad, 0), abs(qgrad)))
        error = float(residual.max())
        scaled = error/scale
        objective = float(g@d + .5*d@H@d)
        slope = float(g@d)
    if (not np.isfinite(qgrad).all()
            or not np.isfinite([error, scaled, objective, slope]).all()):
        raise ValueError('Nonfinite original quadratic/KKT arithmetic')
    if scaled > 1e-10:
        raise ValueError('Bounded least-squares proposal failed original QP KKT check')
    return d, dict(scope='Bounded SPD numerical search model only; not physical equilibrium',
        dimension=len(g), maximum_dimension=19, coordinate_bound_mm=float(limit),
        least_squares_status=int(result.status), least_squares_iterations=int(result.nit),
        maximum_iterations=20*len(g), condition_number=condition,
        objective_value=objective, original_gradient_slope_Nmm=slope,
        gradient_at_solution=qgrad.tolist(), kkt_residual_N=error,
        kkt_scale_N=scale, kkt_scaled_residual=scaled, kkt_scaled_tolerance=1e-10)
