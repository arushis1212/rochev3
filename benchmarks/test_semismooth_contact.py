import unittest
import numpy as np
from physics.semismooth_contact import System, project, small_newton, Rejected

class Tests(unittest.TestCase):

    def coupled(self, case):
        rng = np.random.default_rng(1800 + case)
        q = rng.normal(size=(6, 6)) * 0.08
        K = np.eye(6) + q.T @ q
        B = np.eye(6) + rng.normal(size=(6, 6)) * 0.06
        g0 = rng.normal(size=(2, 3)) * 0.025
        g = np.array([[0.0, 0.12, -0.16], [0.15, 0.03, 0.04]])
        lam = np.array([[2.0, -0.24, 0.32], [0, 0, 0.0]])
        if case % 2:
            g[0, 1:] = 0
            lam[0, 1:] = [-0.13, 0.17]
        u = np.linalg.solve(B, (g - g0).ravel())
        f = K @ u - B.T @ lam.ravel()
        rho = np.array([1.7, 0.9])
        Du = 1 / np.sqrt(np.diag(K + B.T @ np.diag(np.repeat(rho, 3)) @ B))
        return (System(K, B, f, g0, rho, np.array([2.0, 0]), 0.2, Du), u, lam)

    def test_exact_scaled_Jacobian_open_stick_slip(self):
        for case in range(6):
            (sys, u, lam) = self.coupled(case)
            x = sys.pack(u, lam)
            (r, s) = sys.evaluate(x)
            rng = np.random.default_rng(case)
            dx = rng.normal(size=len(x))
            eps = 1e-07
            fd = (sys.evaluate(x + eps * dx)[0] - sys.evaluate(x - eps * dx)[0]) / (2 * eps)
            np.testing.assert_allclose(sys.action(s, dx), fd, atol=2e-08, rtol=2e-07)

    def test_coupled_known_solutions_and_full_merit(self):
        for case in range(12):
            (sys, u, lam) = self.coupled(case)
            (x, history) = small_newton(sys, np.zeros(12))
            (r, s) = sys.evaluate(x)
            self.assertTrue(sys.checks(s)['converged'])
            np.testing.assert_allclose(s['u'], u, atol=2e-07)
            np.testing.assert_allclose(s['lam'], lam, atol=2e-07)
            self.assertTrue(all((b['merit'] <= a['merit'] for (a, b) in zip(history, history[1:]))))

    def test_nonassociated_slip_has_zero_normal_gap(self):
        sys = System(np.eye(3), np.eye(3), np.array([-2.0, 3, 0]), np.zeros((1, 3)), np.array([1.0]), np.array([2.0]), 0.5, np.ones(3) / np.sqrt(2))
        (x, h) = small_newton(sys, np.zeros(6))
        (_, s) = sys.evaluate(x)
        np.testing.assert_allclose(s['u'], [0, 2, 0], atol=1e-08)
        np.testing.assert_allclose(s['lam'], [[2, -1, 0]], atol=1e-08)

    def test_selected_generalized_boundary_derivatives(self):
        y = np.array([[0.0, 1.0, 0.0]])
        (p, J) = project(y, [1.0])
        eps = 1e-07
        for direction in (np.array([[1.0, 0, 0]]), np.array([[0.0, 1, 0]]), np.array([[0.0, 0, 1.0]])):
            fd = (project(y + eps * direction, [1.0])[0] - p) / eps
            np.testing.assert_allclose(np.einsum('nij,nj->ni', J, direction), fd, atol=1e-07)
        (p, J) = project([[0.0, 0, 0]], [0.0])
        np.testing.assert_array_equal(J[0, 1:, 1:], 0)

    def test_restart_pack_and_scale_does_not_change_residual(self):
        (sys, u, lam) = self.coupled(0)
        x = sys.pack(u + 0.01, lam + 0.02)
        (r, s) = sys.evaluate(x)
        x2 = sys.pack(s['u'], s['lam'])
        np.testing.assert_array_equal(x, x2)
        np.testing.assert_array_equal(r, sys.evaluate(x2)[0])

    def test_redundant_dual_rejects_without_pseudoinverse(self):
        B = np.vstack([np.eye(3), np.eye(3)])
        sys = System(np.eye(3), B, np.array([-2.0, 0, 0]), np.zeros((2, 3)), np.ones(2), np.ones(2), 0.5, np.ones(3) / np.sqrt(3))
        with self.assertRaises(Rejected):
            small_newton(sys, np.zeros(9))
if __name__ == '__main__':
    unittest.main()
