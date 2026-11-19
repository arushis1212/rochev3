import unittest

import numpy as np

from physics.bordered_newton import minimize_bordered
from physics.guarded_bfgs import inverse_bfgs_update, options_from_config


class GuardedBFGS(unittest.TestCase):
    def solve(self, f, start, **changes):
        settings = dict(spectral='absolute_damped', maxiter=200, max_step=.25,
                        damping_control={'enabled': True, 'initial_N_per_mm': .1},
                        quasi_newton={'enabled': True, 'refresh_interval': 8,
                                      'newton_below_residual_N': 1e-4})
        return minimize_bordered(f, np.asarray(start, dtype=float), 1, lambda x: True,
                                 **{**settings, **changes})

    def test_positive_update_satisfies_secant_and_remains_positive(self):
        inverse = np.diag([.2, 2., 1.])
        s = np.array([.2, -.3, .1]); y = np.array([1., -.4, .8])
        updated, info = inverse_bfgs_update(inverse, s, y)
        self.assertTrue(info['accepted'])
        np.testing.assert_allclose(updated @ y, s, atol=1e-14)
        self.assertGreater(np.linalg.eigvalsh(updated).min(), 0.)

    def test_negative_and_unresolved_curvature_are_not_installed(self):
        for y in [np.array([-1., 0.]), np.zeros(2), np.array([1e-40, 0.])]:
            updated, info = inverse_bfgs_update(np.eye(2), np.array([1., 0.]), y)
            self.assertIsNone(updated)
            self.assertFalse(info['accepted'])

    def test_disabled_option_preserves_original_path_exactly(self):
        H = np.diag([.03, 80.])
        def f(x): return .5*x@H@x, H@x
        paths = []
        for config in [None, {'enabled': False}]:
            path = []
            self.solve(f, [.2, .2], quasi_newton=config,
                       callback=lambda x, row: path.append(x.copy()))
            paths.append(path)
        np.testing.assert_array_equal(paths[0], paths[1])

    def test_stiff_unilateral_contact_uses_true_force_acceptance(self):
        stiffness = 1e4
        def f(x):
            return (.5*(x[0]+.1)**2+.5*x[1]**2+.5*stiffness*min(x[0], 0.)**2,
                    np.array([x[0]+.1+stiffness*min(x[0], 0.), x[1]]))
        trace = []
        x, result = self.solve(f, [.1, .2], callback=lambda x, row: trace.append(row))
        self.assertTrue(result['optimizer_success'])
        self.assertLessEqual(abs(f(x)[1]).max(), 1e-8)
        self.assertAlmostEqual(x[0], -.1/(1+stiffness), places=10)
        self.assertGreater(result['positive_curvature_updates'], 0)
        self.assertTrue(all(b['energy_Nmm'] <= a['energy_Nmm']+1e-13
                            for a, b in zip(trace, trace[1:])))
        self.assertTrue(all(current['quasi_newton']['fresh_physical_hessian']
                            for previous, current in zip(trace, trace[1:])
                            if previous['residual_N'] <= 1e-4))

    def test_nonconvex_energy_recovers_analytical_minimum(self):
        def f(x):
            return (x[0]*x[0]-1)**2+.5*x[1]**2, np.array([4*x[0]*(x[0]*x[0]-1), x[1]])
        x, result = self.solve(f, [.1, .2])
        self.assertTrue(result['optimizer_success'])
        self.assertAlmostEqual(x[0], 1., places=7)
        self.assertLessEqual(abs(f(x)[1]).max(), 1e-8)

    def test_longer_finite_blocks_keep_analytical_force_and_refresh_contract(self):
        def nonconvex(x):
            return (x[0]*x[0]-1)**2+.5*x[1]**2, np.array([4*x[0]*(x[0]*x[0]-1), x[1]])
        def contact(x):
            return (.5*(x[0]+.1)**2+.5*x[1]**2+5e3*min(x[0], 0.)**2,
                    np.array([x[0]+.1+1e4*min(x[0], 0.), x[1]]))
        for f, target in [(nonconvex, 1.), (contact, -.1/10001)]:
            trace = []
            x, result = self.solve(f, [.1, .2],
                quasi_newton={'enabled': True, 'refresh_interval': 32,
                              'newton_below_residual_N': 1e-4},
                callback=lambda x, row: trace.append(row))
            self.assertTrue(result['optimizer_success'])
            self.assertLessEqual(abs(f(x)[1]).max(), 1e-8)
            self.assertAlmostEqual(x[0], target, places=7)
            self.assertLessEqual(max(row['quasi_newton']['steps_since_refresh'] for row in trace), 32)
            self.assertTrue(all(current['quasi_newton']['fresh_physical_hessian']
                                for previous, current in zip(trace, trace[1:])
                                if previous['residual_N'] <= 1e-4))

    def test_contact_cap_and_physical_guard_apply_to_every_secant_step(self):
        H = np.diag([2., 3.]); accepted = []; calls = []
        def f(x): return .5*x@H@x, H@x
        def guard(a, b):
            calls.append((a.copy(), b.copy()))
            return abs(b-a).max() <= .03000001
        x, result = self.solve(f, [.2, .2], maxiter=100,
                               contact_event_limiter=lambda x, d: {'alpha': .5, 'event_found': True},
                               step_admissible=guard,
                               callback=lambda x, row: accepted.append((x.copy(), row)))
        self.assertTrue(result['optimizer_success'])
        previous = np.array([.2, .2])
        for current, row in accepted:
            self.assertLessEqual(abs(current-previous).max(), .03000001)
            self.assertLessEqual(row['contact_event']['accepted_alpha'], .5)
            self.assertTrue(any(np.array_equal(a, previous) and np.array_equal(b, current)
                                for a, b in calls))
            previous = current

    def test_secant_predictions_are_not_claimed_as_fresh_physical_hessians(self):
        def f(x): return .5*(x[0]**2+x[1]**2), x.copy()
        trace = []
        self.solve(f, [.2, .2], maxiter=3,
                   contact_event_limiter=lambda x, d: {'alpha': .1},
                   callback=lambda x, row: trace.append(row))
        self.assertTrue(trace[0]['quasi_newton']['fresh_physical_hessian'])
        self.assertFalse(trace[1]['quasi_newton']['fresh_physical_hessian'])
        self.assertIsNone(trace[1]['damping_control']['physical_quadratic_predicted_reduction_Nmm'])
        self.assertFalse(trace[1]['quasi_newton']['matrix_checkpointed'])

    def test_verified_clamp_activation_forces_fresh_physical_coupling(self):
        def f(x): return .5*x@x, x.copy()
        event = {'alpha': .1, 'event_found': True, 'verified_buffered_event': True,
                 'event_kind': 'activation', 'selected_monitor': 'moving_clamp'}
        trace = []
        self.solve(f, [.2, .2], maxiter=2,
                   contact_event_limiter=lambda x, d: event.copy(),
                   callback=lambda x, row: trace.append(row))
        self.assertEqual(trace[0]['quasi_newton']['forced_rebuild_reason'], 'verified_new_clamp_contact')
        self.assertTrue(trace[1]['quasi_newton']['fresh_physical_hessian'])

    def test_bad_configuration_is_rejected(self):
        for config in [[], {'enabled': 1}, {'enabled': True, 'refresh_interval': 0},
                       {'enabled': True, 'refresh_interval': 1000},
                       {'enabled': True, 'newton_below_residual_N': float('nan')},
                       {'enabled': True, 'force_tolerance': 1.}]:
            with self.assertRaises(ValueError): options_from_config(config)


if __name__ == '__main__':
    unittest.main()
