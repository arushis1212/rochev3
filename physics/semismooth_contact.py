"""Exact scaled fixed-Tresca projection residual and small dense Newton proof."""
import numpy as np
from physics.unilateral_contact import diagnostics

class Rejected(RuntimeError):
    pass

def project(y, radius):
    y = np.asarray(y, float)
    r = np.asarray(radius, float)
    if y.ndim != 2 or y.shape[1] != 3 or len(y) == 0 or (r.shape != (len(y),)) or (not np.isfinite(y).all()) or (not np.isfinite(r).all()) or (np.min(r) < 0):
        raise ValueError('Finite projection inputs required')
    p = np.zeros_like(y)
    J = np.zeros((len(y), 3, 3))
    p[:, 0] = np.maximum(y[:, 0], 0)
    J[:, 0, 0] = y[:, 0] >= 0
    for i in range(len(y)):
        norm = np.linalg.norm(y[i, 1:])
        if r[i] == 0:
            continue
        if norm < r[i]:
            p[i, 1:] = y[i, 1:]
            J[i, 1:, 1:] = np.eye(2)
        else:
            v = y[i, 1:] / norm
            p[i, 1:] = r[i] * v
            J[i, 1:, 1:] = r[i] / norm * (np.eye(2) - np.outer(v, v))
    return (p, J)

class System:

    def __init__(self, K, B, f, g0, rho, p_old, mu, Du):
        self.K = K
        self.B = B
        self.f = np.asarray(f, float)
        self.g0 = np.asarray(g0, float)
        self.rho = np.asarray(rho, float)
        self.p = np.asarray(p_old, float)
        self.mu = mu
        self.Du = np.asarray(Du, float)
        self.n = K.shape[0]
        self.m = B.shape[0] // 3
        if K.shape != (self.n, self.n) or B.shape != (3 * self.m, self.n) or self.m < 1 or (self.f.shape != (self.n,)) or (self.g0.shape != (self.m, 3)) or (self.rho.shape != (self.m,)) or (self.p.shape != (self.m,)) or (self.Du.shape != (self.n,)):
            raise ValueError('Shape mismatch')
        if isinstance(mu, (bool, np.bool_)) or not np.isscalar(mu) or (not np.isfinite(mu)) or (mu < 0) or (not all((np.isfinite(x).all() for x in (self.f, self.g0, self.rho, self.p, self.Du)))) or (min(self.rho.min(), self.Du.min()) <= 0) or (self.p.min() < 0):
            raise ValueError('Finite positive scales and nonnegative bounds required')
        self.root = np.sqrt(self.rho)

    def pack(self, u, lam):
        return np.r_[np.asarray(u) / self.Du, (np.asarray(lam) / self.root[:, None]).ravel()]

    def evaluate(self, x):
        x = np.asarray(x, float)
        if x.shape != (self.n + 3 * self.m,) or not np.isfinite(x).all():
            raise ValueError('Finite scaled state required')
        u = self.Du * x[:self.n]
        lam = self.root[:, None] * x[self.n:].reshape(-1, 3)
        g = (self.B @ u).reshape(-1, 3) + self.g0
        (p, J) = project(lam - self.rho[:, None] * g, self.mu * self.p)
        eq = self.K @ u - self.f - self.B.T @ lam.ravel()
        c = lam - p
        res = np.r_[self.Du * eq, (c / self.root[:, None]).ravel()]
        return (res, dict(u=u, lam=lam, g=g, eq=eq, c=c, J=J))

    def action(self, state, dx):
        du = self.Du * np.asarray(dx)[:self.n]
        dl = self.root[:, None] * np.asarray(dx)[self.n:].reshape(-1, 3)
        dg = (self.B @ du).reshape(-1, 3)
        dc = dl - np.einsum('nij,nj->ni', state['J'], dl - self.rho[:, None] * dg)
        return np.r_[self.Du * (self.K @ du - self.B.T @ dl.ravel()), (dc / self.root[:, None]).ravel()]

    def checks(self, state):
        d = diagnostics(self.K, self.B, self.f, state['u'], state['lam'], self.g0, self.mu * self.p)
        d['projection_residual_N'] = float(np.max(abs(state['c'])))
        d['converged'] = bool(d['equilibrium_inf_N'] <= 1e-07 and d['projection_residual_N'] <= 1e-07 and (d['minimum_average_gap_mm'] >= -1e-08) and (d['minimum_normal_resultant_N'] >= -1e-07) and (d['normal_complementarity_Nmm'] <= 1e-08) and (d['maximum_flow_residual_N'] <= 1e-07))
        return d

def small_newton(system, x, maximum=40):
    x = np.asarray(x, float).copy()
    history = []
    for iteration in range(maximum):
        (r, s) = system.evaluate(x)
        d = system.checks(s)
        merit = float(0.5 * r @ r)
        history.append(dict(iteration=iteration, merit=merit, **d))
        if d['converged']:
            return (x, history)
        eye = np.eye(len(x))
        J = np.column_stack([system.action(s, col) for col in eye])
        rank = np.linalg.matrix_rank(J)
        if rank < len(x):
            raise Rejected(('Singular generalized Jacobian, no regularization', rank, len(x), history))
        direction = np.linalg.solve(J, -r)
        if np.max(abs(J @ direction + r)) > 1e-09 * max(1, np.max(abs(r))):
            raise Rejected('Newton linear residual')
        accepted = False
        for backtrack in range(20):
            alpha = 2.0 ** (-backtrack)
            trial = x + alpha * direction
            (rr, _) = system.evaluate(trial)
            if 0.5 * rr @ rr <= (1 - 0.0001 * alpha) * merit:
                x = trial
                accepted = True
                history[-1].update(step=alpha)
                break
        if not accepted:
            raise Rejected(('Complete force/contact merit line search failed', history))
    raise Rejected(('Newton iteration bound', history))
