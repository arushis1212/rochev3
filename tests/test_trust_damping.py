import unittest
import numpy as np
from physics.bordered_newton import minimize_bordered
from physics.trust_damping import AbsoluteDampingControl, damping_from_config
from physics.contact_events import ContactEventLimiter
from tests.test_contact_events import prepared


class TrustDamping(unittest.TestCase):
    def update(self, control, **changes):
        args = dict(used=1., old_energy=10., new_energy=9., predicted_reduction=1.,
                    accepted_alpha=1., proposed_cap_alpha=1., numerical_floor=1e-9,
                    hessian_scale=100.)
        return control.update(**{**args, **changes})

    def test_small_verified_contact_cap_alone_holds_damping(self):
        control = AbsoluteDampingControl()
        row = self.update(control, accepted_alpha=1e-4, proposed_cap_alpha=1e-4)
        self.assertEqual(row['action'], 'hold')
        self.assertEqual(row['next_damping_N_per_mm'], 1.)
        self.assertEqual(row['backtracking_fraction_relative_to_cap'], 1.)

    def test_actual_backtracking_relative_to_contact_cap_increases_damping(self):
        row = self.update(AbsoluteDampingControl(), accepted_alpha=1e-5, proposed_cap_alpha=1e-4)
        self.assertEqual(row['reason'], 'backtracking_relative_to_cap')
        self.assertEqual(row['next_damping_N_per_mm'], 4.)

    def test_good_capped_fractions_accumulate_before_decaying(self):
        control = AbsoluteDampingControl(accumulate_good_capped_steps=True)
        for _ in range(9):
            row = self.update(control, accepted_alpha=.1, proposed_cap_alpha=.1)
            self.assertEqual(row['action'], 'hold')
        row = self.update(control, accepted_alpha=.1, proposed_cap_alpha=.1)
        self.assertEqual(row['action'], 'decay')
        self.assertEqual(row['reason'], 'accumulated_good_capped_trials')
        self.assertEqual(row['next_good_step_credit'], 0.)
        self.assertEqual(row['next_damping_N_per_mm'], .5)

    def test_backtracking_or_bad_model_clears_accumulated_credit(self):
        for changes in [dict(accepted_alpha=.05, proposed_cap_alpha=.1),
                        dict(accepted_alpha=.1, proposed_cap_alpha=.1, new_energy=9.9)]:
            control = AbsoluteDampingControl(accumulate_good_capped_steps=True,
                                             initial_good_step_credit=.8)
            row = self.update(control, **changes)
            self.assertEqual(row['next_good_step_credit'], 0.)

    def test_saved_partial_credit_resumes_without_releasing_metric_early(self):
        control = damping_from_config({'enabled': True, 'initial_N_per_mm': .03125,
                                      'accumulate_good_capped_steps': True,
                                      'initial_good_step_credit': .8})
        row = self.update(control, used=.03125, accepted_alpha=.1, proposed_cap_alpha=.1)
        self.assertEqual(row['action'], 'hold')
        row = self.update(control, used=.03125, accepted_alpha=.1, proposed_cap_alpha=.1)
        self.assertEqual(row['action'], 'decay')
        self.assertEqual(row['next_damping_N_per_mm'], .015625)
        for credit in [-.1, 1., float('nan')]:
            with self.assertRaises(ValueError):
                AbsoluteDampingControl(accumulate_good_capped_steps=True,
                                       initial_good_step_credit=credit)

    def test_poor_physical_quadratic_agreement_increases_damping(self):
        row = self.update(AbsoluteDampingControl(), new_energy=9.9)
        self.assertEqual(row['reason'], 'poor_quadratic_agreement')
        self.assertAlmostEqual(row['actual_to_predicted_reduction'], .1)
        self.assertEqual(row['next_damping_N_per_mm'], 4.)

    def test_good_full_step_decays_and_roundoff_can_remove_final_regularization(self):
        control = AbsoluteDampingControl()
        self.assertEqual(self.update(control)['next_damping_N_per_mm'], .5)
        row = self.update(control, used=1e-9, old_energy=1e8, new_energy=1e8,
                          predicted_reduction=1e-10)
        self.assertIsNone(row['actual_to_predicted_reduction'])
        self.assertEqual(row['reason'], 'roundoff_limited_full_trial')
        self.assertEqual(row['next_damping_N_per_mm'], 0.)

    def test_unknown_or_invalid_settings_fail_before_optimization(self):
        self.assertIsNone(damping_from_config(None))
        self.assertIsNone(damping_from_config({'enabled': False}))
        for config in [{'enabled': 1}, {'enabled': True, 'initial_N_per_mm': -1.},
                       {'enabled': True, 'initial_N_per_mm': float('nan')},
                       {'enabled': True, 'secret_force_threshold': 1.}, []]:
            with self.assertRaises(ValueError):
                damping_from_config(config)
        with self.assertRaisesRegex(ValueError, 'absolute_damped'):
            minimize_bordered(lambda x: (0., x), np.ones(2), 1, lambda x: True,
                              damping_control={'enabled': True})

    def test_disabled_control_preserves_original_iterates_exactly(self):
        H = np.diag([.03, 80.])
        def f(x):
            return .5*x@H@x, H@x
        paths = []
        for config in [None, {'enabled': False}]:
            path = []
            x, result = minimize_bordered(f, np.array([.2, .2]), 1, lambda x: True,
                                          spectral='absolute_damped', damping_control=config,
                                          callback=lambda x, info: path.append(x.copy()))
            paths.append(path)
        np.testing.assert_array_equal(paths[0], paths[1])
        self.assertTrue(result['optimizer_success'])

    def test_stiff_unilateral_penalty_converges_at_original_force_threshold(self):
        stiffness = 1e4
        def f(x):
            return (.5*(x[0]+.1)**2+.5*x[1]**2+.5*stiffness*min(x[0], 0.)**2,
                    np.array([x[0]+.1+stiffness*min(x[0], 0.), x[1]]))
        limiter = ContactEventLimiter(lambda x, d: prepared(lambda a: x[0]+a*d[0], abs(d[0])))
        trace = []
        x, result = minimize_bordered(f, np.array([.1, .2]), 1, lambda x: True,
                                      spectral='absolute_damped', damping_control={'enabled': True, 'accumulate_good_capped_steps': True},
                                      contact_event_limiter=limiter, maxiter=60,
                                      callback=lambda x, row: trace.append(row))
        self.assertTrue(result['optimizer_success'])
        self.assertLessEqual(abs(f(x)[1]).max(), 1e-8)
        self.assertAlmostEqual(x[0], -.1/(1+stiffness), places=10)
        self.assertGreater(result['damping_control']['decays'], 0)
        self.assertTrue(all(b['energy_Nmm'] <= a['energy_Nmm']+1e-13 for a, b in zip(trace, trace[1:])))

    def test_nonconvex_descent_recovers_known_minimum_and_persists_metric(self):
        def f(x):
            return (x[0]*x[0]-1)**2+.5*x[1]*x[1], np.array([4*x[0]*(x[0]*x[0]-1), x[1]])
        trace = []
        x, result = minimize_bordered(f, np.array([.1, .2]), 1, lambda x: True,
                                      maxiter=80, spectral='absolute_damped',
                                      damping_control={'enabled': True, 'initial_N_per_mm': 1., 'accumulate_good_capped_steps': True},
                                      callback=lambda x, row: trace.append(row))
        self.assertTrue(result['optimizer_success'])
        self.assertAlmostEqual(x[0], 1., places=7)
        self.assertLessEqual(abs(f(x)[1]).max(), 1e-8)
        self.assertTrue(all(b['energy_Nmm'] <= a['energy_Nmm']+1e-13 for a, b in zip(trace, trace[1:])))
        for first, second in zip(trace, trace[1:]):
            self.assertGreaterEqual(second['damping_control']['used_damping_N_per_mm'],
                                    first['damping_control']['next_damping_N_per_mm'])
        self.assertGreater(result['damping_control']['decays'], 0)

    def test_physical_quadratic_prediction_uses_original_not_regularized_hessian(self):
        H = np.diag([2., 8.])
        start = np.array([.2, -.1])
        def f(x):
            return .5*x@H@x, H@x
        trace = []
        x, result = minimize_bordered(f, start, 1, lambda x: True, maxiter=1,
                                      spectral='absolute_damped', damping_control={'enabled': True},
                                      callback=lambda x, row: trace.append(row))
        delta = x-start
        expected = -(H@start)@delta-.5*delta@H@delta
        row = trace[0]['damping_control']
        self.assertAlmostEqual(row['physical_quadratic_predicted_reduction_Nmm'], expected, places=11)
        self.assertAlmostEqual(row['actual_to_predicted_reduction'], 1., places=9)


if __name__ == '__main__':
    unittest.main()
