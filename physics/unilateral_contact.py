"""Small-displacement unilateral contact: fixed Tresca ADMM and a checked Coulomb outer iteration."""
import time
import numpy as np

class Stop(RuntimeError):
    pass

def prox_gap(y, bounds, rho):
    y = np.asarray(y, float)
    b = np.asarray(bounds, float)
    r = np.asarray(rho, float)
    if y.ndim != 2 or y.shape[1] != 3 or b.shape != (len(y),) or (r.shape != (len(y),)) or (not all((np.isfinite(v).all() for v in (y, b, r)))) or (np.min(b) < 0) or (np.min(r) <= 0):
        raise ValueError('Finite positive rho and nonnegative Tresca bounds required')
    z = y.copy()
    z[:, 0] = np.maximum(y[:, 0], 0)
    norm = np.linalg.norm(y[:, 1:], axis=1)
    scale = np.maximum(0, 1 - b / (r * np.maximum(norm, 1e-300)))
    z[:, 1:] *= scale[:, None]
    return z

def diagnostics(K, B, f, u, lam, g0, bounds):
    g = np.asarray(B @ u).reshape(-1, 3) + g0
    eq = np.asarray(K @ u - f - B.T @ lam.ravel())
    norm = np.linalg.norm(g[:, 1:], axis=1)
    shear = np.linalg.norm(lam[:, 1:], axis=1)
    sliding = norm > 1e-08
    flow = np.zeros(len(g))
    flow[sliding] = np.linalg.norm(lam[sliding, 1:] + bounds[sliding, None] * g[sliding, 1:] / norm[sliding, None], axis=1)
    flow[~sliding] = np.maximum(shear[~sliding] - bounds[~sliding], 0)
    return dict(equilibrium_inf_N=float(np.max(abs(eq))), minimum_average_gap_mm=float(g[:, 0].min()), minimum_normal_resultant_N=float(lam[:, 0].min()), normal_complementarity_Nmm=float(np.max(abs(lam[:, 0] * g[:, 0]))), maximum_Tresca_excess_N=float(np.max(np.maximum(shear - bounds, 0))), maximum_flow_residual_N=float(flow.max()), friction_work_Nmm=float(np.sum(lam[:, 1:] * g[:, 1:])), dissipation_Nmm=float(np.sum(bounds * norm)))

def fixed_tresca(K, B, f, g0, rho, p_old, mu, solve, state, *, maximum=80, gap_tol=1e-08, force_tol=1e-07, comp_tol=1e-08, deadline=None, progress=None):
    g0 = np.asarray(g0, float)
    rho = np.asarray(rho, float)
    p = np.asarray(p_old, float)
    if isinstance(mu, (bool, np.bool_)) or not np.isscalar(mu) or (not np.isfinite(mu)) or (mu < 0) or (p.shape != rho.shape) or (g0.shape != (len(p), 3)) or (np.min(p) < 0) or (np.min(rho) <= 0) or (not all((np.isfinite(x).all() for x in (g0, rho, p)))):
        raise ValueError('Invalid fixed Tresca data')
    if isinstance(maximum, (bool, np.bool_)) or not isinstance(maximum, (int, np.integer)) or maximum < 1:
        raise ValueError('Positive iteration count required')
    if any((not np.isscalar(x) or isinstance(x, (bool, np.bool_)) or (not np.isfinite(x)) or (x <= 0) for x in (gap_tol, force_tol, comp_tol))):
        raise ValueError('Positive finite residual tolerances required')
    u = np.array(state['u'], float)
    z = np.array(state['z'], float)
    lam = np.array(state['lambda'], float)
    bounds = mu * p
    record = None
    for iteration in range(maximum):
        if deadline is not None and time.monotonic() >= deadline:
            raise Stop('ADMM deadline')
        rhs = f + B.T @ (lam + rho[:, None] * (z - g0)).ravel()
        u = solve(np.asarray(rhs), u)
        g = np.asarray(B @ u).reshape(-1, 3) + g0
        y = g - lam / rho[:, None]
        z = prox_gap(y, bounds, rho)
        lam = lam - rho[:, None] * (g - z)
        record = diagnostics(K, B, f, u, lam, g0, bounds)
        record.update(iteration=iteration + 1, primal_gap_residual_mm=float(np.max(abs(g - z))))
        state.update(u=u, z=z, **{'lambda': lam})
        if progress:
            progress(record, state)
        if record['primal_gap_residual_mm'] <= gap_tol and record['equilibrium_inf_N'] <= force_tol and (record['normal_complementarity_Nmm'] <= comp_tol) and (record['minimum_average_gap_mm'] >= -gap_tol) and (record['minimum_normal_resultant_N'] >= -force_tol) and (record['maximum_flow_residual_N'] <= force_tol):
            return dict(converged=True, **record)
    return dict(converged=False, **record)

def coulomb_step(K, B, f, g0, rho, mu, p_start, solve, state, *, outer_max=12, outer_tol=1e-07, progress=None, **inner):
    p = np.asarray(p_start, float).copy()
    records = []
    for outer in range(outer_max):
        result = fixed_tresca(K, B, f, g0, rho, p, mu, solve, state, progress=(lambda row, st: progress(dict(outer=outer + 1, **row), st)) if progress else None, **inner)
        mismatch = float(np.max(abs(state['lambda'][:, 0] - p)))
        records.append(dict(outer=outer + 1, normal_bound_mismatch_N=mismatch, **result))
        if not result['converged']:
            return dict(converged=False, reason='Inner Tresca solve incomplete', records=records)
        if mismatch <= outer_tol:
            actual = diagnostics(K, B, f, state['u'], state['lambda'], g0, mu * np.maximum(state['lambda'][:, 0], 0))
            return dict(converged=actual['maximum_Tresca_excess_N'] <= outer_tol and actual['maximum_flow_residual_N'] <= outer_tol, reason='Coulomb fixed-point checked with actual normal force', records=records, actual_Coulomb=actual)
        p = 0.5 * (p + np.maximum(state['lambda'][:, 0], 0))
    return dict(converged=False, reason='Coulomb outer fixed point incomplete', records=records)
