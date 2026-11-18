"""Analytical and exhaustive references for finite search quadratics."""
import itertools
import unittest
import numpy as np

from physics.convex_search import boxed_spd_direction, quadratic_direction


class ConvexSearchTests(unittest.TestCase):
    def test_box_interior_and_boundary(self):
        H = np.array([[4., 1.], [1., 2.]])
        g = np.array([.5, -.5])
        d, _ = boxed_spd_direction(H, g, 1.)
        np.testing.assert_allclose(d, -np.linalg.solve(H, g), atol=1e-14)
        d, _ = boxed_spd_direction(np.diag([2., 3.]), [10., -12.], .1)
        np.testing.assert_array_equal(d, [-.1, .1])

    def test_box_face_optimum_is_not_uniform_scaling(self):
        H = np.array([[10., 2.], [2., 1.]])
        g = np.array([-3., -.1])
        d, _ = boxed_spd_direction(H, g, .2)
        np.testing.assert_allclose(d, [.2, -.2], atol=1e-14)
        gradient = H @ d + g
        self.assertLessEqual(gradient[0], 0.)
        self.assertGreaterEqual(gradient[1], 0.)

    def test_box_rejects_indefinite_or_nonfinite_data(self):
        for H in (np.diag([1., -1.]), np.array([[1., 0.], [0., np.inf]])):
            with self.assertRaises(ValueError):
                boxed_spd_direction(H, [1., 1.], .1)

    def test_one_hinge_analytical_solution(self):
        # Q(d)=2d+d^2/2+3*min(.5+d,0)^2/2.
        # Active branch gives d=-(2+3*.5)/(1+3)=-.875.
        d, info = quadratic_direction(np.eye(1), np.array([2.]),
            np.array([.5]), np.ones((1, 1)), np.array([3.]), solver='dual_nnls')
        self.assertTrue(info['success'])
        np.testing.assert_allclose(d, [-.875], atol=1e-13)

    def test_inactive_hinge_and_empty_set(self):
        for gap, J, k in ((np.array([5.]), np.ones((1, 1)), np.array([100.])),
                          (np.empty(0), np.empty((0, 1)), np.empty(0))):
            d, info = quadratic_direction(np.eye(1), np.array([1.]), gap, J, k,
                                         solver='dual_nnls')
            self.assertTrue(info['success'])
            np.testing.assert_allclose(d, [-1.], atol=1e-13)

    def test_dual_against_exhaustive_active_sets(self):
        rng = np.random.default_rng(82714)
        for _ in range(40):
            Z = rng.normal(size=(4, 4)); M = Z.T @ Z + np.eye(4)
            A = np.linalg.inv(M); g = rng.normal(size=4)
            J = rng.normal(size=(5, 4)); gap = rng.uniform(0., .6, 5)
            k = rng.uniform(.1, 20., 5)
            candidates = []
            for bits in itertools.product((False, True), repeat=5):
                mask = np.array(bits)
                H = M + J[mask].T @ (k[mask, None] * J[mask])
                rhs = g + J[mask].T @ (k[mask] * gap[mask])
                d = -np.linalg.solve(H, rhs)
                gaps = gap + J @ d
                if np.all(gaps[mask] <= 1e-10) and np.all(gaps[~mask] >= -1e-10):
                    candidates.append(d)
            self.assertTrue(candidates)
            d, info = quadratic_direction(A, g, gap, J, k, solver='dual_nnls')
            self.assertTrue(info['success'])
            np.testing.assert_allclose(d, candidates[0], rtol=1e-10, atol=1e-11)
            self.assertLessEqual(info['dual_diagnostics']['kkt_scaled_residual'], 1e-9)

    def test_force_model_is_not_modified(self):
        arrays = (np.eye(2), np.array([1., 2.]), np.array([.2]),
                  np.array([[1., -1.]]), np.array([3.]))
        copies = [a.copy() for a in arrays]
        _, info = quadratic_direction(*arrays, solver='dual_nnls')
        for original, copy in zip(arrays, copies):
            np.testing.assert_array_equal(original, copy)
        self.assertFalse(info['physical_energy_or_gradient_modified'])


if __name__ == '__main__':
    unittest.main()
