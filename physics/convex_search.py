"""Finite convex search proposals for constrained numerical mechanics.

The caller supplies its objective gradient and positive search metric. These
helpers propose steps; the caller still evaluates its original objective and
physical constraints before accepting a candidate. Units must be consistent.
"""
import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from scipy.optimize import nnls

def boxed_spd_direction(matrix, gradient, limit):
    """Exact one/two-variable SPD quadratic minimum on the coordinate box.

    A minimum is either the feasible unconstrained minimum or lies on a face.
    Each face is a one-variable convex quadratic, whose clipped minimum also
    covers its two corners. This is a search model, not a physical energy.
    """
    H=np.array(matrix,dtype=float,copy=True);g=np.array(gradient,dtype=float,copy=True)
    if (g.ndim!=1 or len(g)not in (1,2) or H.shape!=(len(g),len(g))
            or not np.isfinite(H).all() or not np.isfinite(g).all()
            or not np.array_equal(H,H.T) or isinstance(limit,bool)
            or not np.isfinite(limit) or limit<=0):
        raise ValueError('Finite symmetric one/two-variable box quadratic required')
    eigenvalues=np.linalg.eigvalsh(H)
    if not np.isfinite(eigenvalues).all() or eigenvalues.min()<=0:
        raise ValueError('Positive-definite box search matrix required')
    candidates=[np.zeros(len(g))]
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        unconstrained=-np.linalg.solve(H,g)
        if not np.isfinite(unconstrained).all():
            raise ValueError('Nonfinite unconstrained box search candidate')
        if np.max(abs(unconstrained))<=limit:candidates.append(unconstrained)
        for j in range(len(g)):
            for sign in (-1.,1.):
                value=np.zeros(len(g));value[j]=sign*limit
                if len(g)==2:
                    k=1-j
                    free=-(g[k]+H[k,j]*value[j])/H[k,k]
                    if not np.isfinite(free):raise ValueError('Nonfinite box-face stationary point')
                    value[k]=np.clip(free,-limit,limit)
                candidates.append(value)
        values=np.array([g@d+.5*d@H@d for d in candidates],float)
    if not np.isfinite(values).all() or not all(np.isfinite(v).all()for v in candidates):
        raise ValueError('Nonfinite box quadratic candidate or model value')
    selected=int(np.argmin(values)) # Stable order resolves floating-point ties.
    return candidates[selected].copy(),dict(candidate_displacements_mm=[v.tolist()for v in candidates],
        candidate_model_values_Nmm=values.tolist(),selected_candidate=selected,
        coordinate_bound_mm=float(limit),scope='Exact minimum of bounded local SPD search quadratic only')



def _dual_hinge_direction(A, g, gap, J, K, d0, max_iterations):
    """Finite dual NNLS solve of the same convex affine-gap search quadratic.

    p >= 0, Q=I+U A U.T, b=sqrt(K)*gap+U*d0; d=d0+A U.T*p.
    Numerical KKT checks qualify this proposal only, never physical forces.
    """
    if not len(gap):
        return d0.copy(), True, {'iterations_limit': max_iterations, 'rows': 0,
                                'kkt_scaled_residual': 0., 'reason': 'no_contact_rows'}
    with np.errstate(over='ignore', invalid='ignore'):
        U = np.sqrt(K)[:, None]*J
        AU = A@U.T
        raw_Q = np.eye(len(gap))+U@AU
        Q = .5*raw_Q+.5*raw_Q.T
        b = np.sqrt(K)*gap+U@d0
    if not all(np.isfinite(v).all() for v in (U, AU, Q, b)):
        raise ValueError('Nonfinite dual contact-search system')
    L = np.linalg.cholesky(Q)
    target = -solve_triangular(L, b, lower=True, check_finite=False)
    if not np.isfinite(target).all():
        raise ValueError('Nonfinite dual least-squares target')
    try:
        p, norm = nnls(L.T, target, maxiter=max_iterations)
    except RuntimeError:
        return d0.copy(), False, {'iterations_limit': max_iterations, 'rows': len(gap),
                                  'reason': 'finite_nnls_iteration_limit'}
    with np.errstate(over='ignore', invalid='ignore'):
        Qp = Q@p
        w = Qp+b
        direction = d0+AU@p
        complementarity = p*w
    if (not all(np.isfinite(v).all() for v in (p, Qp, w, direction, complementarity))
            or not np.isfinite(norm) or np.any(p < 0)):
        raise ValueError('Invalid dual solution, reconstruction or diagnostics')
    scale = max(1., float(abs(b).max()), float(abs(Qp).max()))
    kkt = max(float(np.maximum(-w, 0).max()),
              float(abs(complementarity).max())/max(1., float(abs(p).max())))
    scaled = kkt/scale
    success = scaled <= 1e-9
    return direction if success else d0.copy(), success, {
        'iterations_limit': max_iterations, 'rows': len(gap),
        'reason': 'dual_kkt_admitted' if success else 'dual_kkt_residual',
        'dual_variables': p.tolist(), 'dual_gradient': w.tolist(),
        'kkt_scaled_residual': scaled, 'kkt_scale': scale,
        'kkt_search_tolerance': 1e-9, 'least_squares_residual_norm': float(norm),
        'kkt_scope': 'Numerical dual of the selected search quadratic only; not physical force acceptance'}



def quadratic_direction(metric_inverse, gradient, gaps, jacobian, stiffness, *,
                        mode='linearized_hinge', max_active_updates=12,
                        gap_tolerance_mm=1e-12, solver='simultaneous_active_set',
                        dual_max_iterations=128):
    """Solve a small contact-augmented quadratic via Woodbury updates.

    The `linearized_hinge` model is
      g.d + .5*d.M.d + .5*sum K*min(gap + J.d, 0)^2.
    M is the caller's positive search metric, not a claimed physical Hessian.
    `zero_offset_psd` is a comparison regularizer .5*sum K*(J.d)^2;
    it can impede closing positive gaps and is not the hinge model.

    Finite active-set cycling/non-descent fails back to the original direction.
    Callers still enforce their step bound, exact energy and complete guards.
    """
    if solver not in ('simultaneous_active_set', 'dual_nnls'):
        raise ValueError('Explicit supported contact-search solver required')
    if type(dual_max_iterations) is not int or not 1 <= dual_max_iterations <= 512:
        raise ValueError('Finite dual NNLS iteration limit required')
    if solver == 'dual_nnls' and mode != 'linearized_hinge':
        raise ValueError('Dual NNLS solves the affine hinge model only')
    A = np.asarray(metric_inverse, float)
    g = np.asarray(gradient, float)
    gap = np.asarray(gaps, float)
    J = np.asarray(jacobian, float)
    K = np.asarray(stiffness, float)
    if (g.ndim != 1 or A.shape != (len(g), len(g)) or gap.ndim != 1
            or K.shape != gap.shape or J.shape != (len(gap), len(g))
            or not all(np.isfinite(v).all() for v in (A, g, gap, J, K))
            or np.any(gap < 0) or np.any(K <= 0)):
        raise ValueError('Finite inactive contact rows and positive weights required')
    if mode not in ('linearized_hinge', 'zero_offset_psd'):
        raise ValueError('Explicit supported search-quadratic mode required')
    if type(max_active_updates) is not int or max_active_updates < 1:
        raise ValueError('Positive integer active-set limit required')
    if not np.isfinite(gap_tolerance_mm) or gap_tolerance_mm < 0:
        raise ValueError('Finite nonnegative active-set tolerance required')
    if not np.allclose(A, A.T, atol=1e-12, rtol=1e-12):
        raise ValueError('Symmetric positive definite search inverse required')
    if solver == 'dual_nnls':
        # Use one exactly symmetric metric throughout the opt-in dual model.
        # allclose alone permits substantial relative skew on a tiny inverse.
        A = .5*A+.5*A.T
        if not np.isfinite(A).all():
            raise ValueError('Nonfinite canonical dual search inverse')
        factor = cho_factor(A, lower=True, check_finite=False)
        if not np.isfinite(factor[0]).all():
            raise ValueError('Nonfinite canonical dual search factor')
    else:
        factor = cho_factor((A+A.T)/2, lower=True, check_finite=False)
    d0 = -A@g
    if not np.isfinite(d0).all():
        raise ValueError('Finite original search direction required')
    if solver == 'dual_nnls' and len(gap) > 128:
        raise ValueError('Dual NNLS permits at most 128 selected contact rows')
    active = np.ones(len(gap), bool) if mode == 'zero_offset_psd' else gap+J@d0 < 0
    history = []
    seen = set()
    success = False
    d = d0.copy()
    dual_info = None
    if solver == 'dual_nnls':
        d, success, dual_info = _dual_hinge_direction(A, g, gap, J, K, d0, dual_max_iterations)
    else:
        for iteration in range(max_active_updates):
            identity = tuple(np.flatnonzero(active))
            if identity in seen:
                break
            seen.add(identity)
            with np.errstate(over='ignore', invalid='ignore'):
                U = np.sqrt(K[active])[:, None]*J[active]
                AU = A@U.T
                small = np.eye(len(U))+U@AU
                rhs = U@d0
                if mode == 'linearized_hinge':
                    rhs += np.sqrt(K[active])*gap[active]
            if not all(np.isfinite(v).all() for v in (U, AU, small, rhs)):
                raise ValueError('Nonfinite contact search-system arithmetic')
            d = d0-AU@np.linalg.solve(small, rhs)
            linear_gap = gap+J@d
            if not np.isfinite(d).all() or not np.isfinite(linear_gap).all():
                raise ValueError('Nonfinite contact-augmented direction or gap')
            consistent = (mode == 'zero_offset_psd' or
                          (np.all(linear_gap[active] <= gap_tolerance_mm)
                           and np.all(linear_gap[~active] >= -gap_tolerance_mm)))
            history.append(dict(active_rows=[int(value)for value in identity], linear_gaps_mm=linear_gap.tolist(),
                                consistent=bool(consistent)))
            if consistent:
                success = True
                break
            active = (linear_gap < -gap_tolerance_mm) | (active & (linear_gap <= gap_tolerance_mm))
    with np.errstate(over='ignore', invalid='ignore'):
        slope = float(g@d)
    if not np.isfinite(slope):
        raise ValueError('Nonfinite true-gradient directional derivative')
    if not success or (np.any(g != 0) and slope >= 0):
        d = d0.copy()
        success = False
    Md = cho_solve(factor, d, check_finite=False)
    linear_gap = gap+J@d
    penalty_model = (np.minimum(linear_gap, 0) if mode == 'linearized_hinge' else J@d)
    with np.errstate(over='ignore', invalid='ignore'):
        slope = float(g@d)
        value = float(slope+.5*d@Md+.5*np.dot(K*penalty_model, penalty_model))
    if (not np.isfinite(Md).all() or not np.isfinite(linear_gap).all()
            or not np.isfinite(slope) or not np.isfinite(value)):
        raise ValueError('Nonfinite search-quadratic diagnostics')
    return d, dict(mode=mode, solver=solver, dual_diagnostics=dual_info, success=success, fallback=None if success else 'finite_active_set_or_descent',
                   active_set_history=history, quadratic_model_value_Nmm=value,
                   actual_gradient_directional_derivative_Nmm=slope,
                   max_direction_mm=float(abs(d).max(initial=0.)),
                   physical_energy_or_gradient_modified=False,
                   exact_physical_hessian_claimed=False,
                   finite_difference_contact_curvature_may_already_be_present=True,
                   all_future_contact_coverage_claimed=False)

