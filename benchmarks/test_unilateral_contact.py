import unittest
import numpy as np
from physics.unilateral_contact import fixed_tresca, coulomb_step, prox_gap

class Tests(unittest.TestCase):

    def solve_case(self, f, p=2.0, mu=0.5, old=None):
        K = np.eye(3)
        B = np.eye(3)
        rho = np.array([1.0])
        g0 = np.zeros((1, 3))
        if old is not None:
            g0[0, 1:] = -old[1:]
        A = K + B.T @ np.diag(np.repeat(rho, 3)) @ B
        solve = lambda rhs, previous: np.linalg.solve(A, rhs)
        state = {'u': np.zeros(3), 'z': np.zeros((1, 3)), 'lambda': np.zeros((1, 3))}
        result = fixed_tresca(K, B, np.array(f), g0, rho, np.array([p]), mu, solve, state, maximum=200)
        return (state, result)

    def test_sliding_has_zero_normal_gap_no_dilatancy(self):
        s, r = self.solve_case([-2, 3, 0])
        self.assertTrue(r['converged'])
        np.testing.assert_allclose(s['u'], [0, 2, 0], atol=1e-07)
        np.testing.assert_allclose(s['lambda'], [[2, -1, 0]], atol=1e-07)
        self.assertLess(r['friction_work_Nmm'], 0)
        self.assertAlmostEqual(r['friction_work_Nmm'] + r['dissipation_Nmm'], 0, places=7)

    def test_stick_carries_tangent_force_below_bound(self):
        s, r = self.solve_case([-2, 0.25, 0])
        self.assertTrue(r['converged'])
        np.testing.assert_allclose(s['u'], 0, atol=1e-07)
        np.testing.assert_allclose(s['lambda'], [[2, -0.25, 0]], atol=1e-07)

    def test_open_contact_has_no_normal_reaction(self):
        s, r = self.solve_case([2, 0, 0], p=0)
        self.assertTrue(r['converged'])
        np.testing.assert_allclose(s['u'], [2, 0, 0], atol=1e-07)
        np.testing.assert_allclose(s['lambda'], 0, atol=1e-07)

    def test_reversal_uses_previous_displacement_anchor(self):
        s, r = self.solve_case([-2, 3, 0])
        q, t = self.solve_case([-2, -3, 0], old=s['u'])
        self.assertTrue(t['converged'])
        np.testing.assert_allclose(q['u'], [0, -2, 0], atol=1e-07)
        self.assertGreater(q['lambda'][0, 1], 0)

    def test_separate_Coulomb_outer_iteration(self):
        K = B = np.eye(3)
        rho = np.array([1.0])
        s = {'u': np.zeros(3), 'z': np.zeros((1, 3)), 'lambda': np.zeros((1, 3))}
        r = coulomb_step(K, B, np.array([-2.0, 3, 0]), np.zeros((1, 3)), rho, 0.5, np.array([0.1]), lambda rhs, previous: rhs / 2, s, outer_max=40, maximum=200)
        self.assertTrue(r['converged'])
        np.testing.assert_allclose(s['u'], [0, 2, 0], atol=1e-06)

    def test_resultant_area_units_scaling(self):
        y = np.array([[-0.2, 1.0, 0]])
        np.testing.assert_allclose(prox_gap(y, [2.0], [4.0]), prox_gap(y, [4.0], [8.0]))

    def test_invalid_prox_inputs(self):
        for b, r in ([[-1.0], [1.0]], [[1.0], [0.0]], [[np.nan], [1.0]]):
            with self.assertRaises(ValueError):
                prox_gap([[0.0, 0, 0]], b, r)

    def test_coupled_manufactured_mixed_contacts(self):
        rng = np.random.default_rng(824912)
        for case in range(12):
            with self.subTest(case=case):
                q = rng.normal(size=(6, 6)) * 0.08
                K = np.eye(6) + q.T @ q
                B = np.eye(6) + rng.normal(size=(6, 6)) * 0.06
                g0 = rng.normal(size=(2, 3)) * 0.025
                gap = np.array([[0.0, 0.12, -0.16], [0.15, 0.03, 0.04]])
                if case % 2:
                    gap[0, 1:] = 0
                expected_lambda = np.zeros((2, 3))
                expected_lambda[0, 0] = 2.0
                expected_lambda[0, 1:] = [-0.24, 0.32] if case % 2 == 0 else [-0.13, 0.17]
                expected_u = np.linalg.solve(B, (gap - g0).ravel())
                f = K @ expected_u - B.T @ expected_lambda.ravel()
                rho = np.array([1.7, 0.9])
                A = K + B.T @ np.diag(np.repeat(rho, 3)) @ B
                state = {'u': np.zeros(6), 'z': np.zeros((2, 3)), 'lambda': np.zeros((2, 3))}
                result = fixed_tresca(K, B, f, g0, rho, np.array([2.0, 0.0]), 0.2,
                                      lambda rhs, previous: np.linalg.solve(A, rhs), state, maximum=1000)
                self.assertTrue(result['converged'])
                np.testing.assert_allclose(state['u'], expected_u, atol=1e-6)
                np.testing.assert_allclose(state['lambda'], expected_lambda, atol=1e-6)


if __name__ == '__main__':
    unittest.main()
