"""Contact event controls preserve the physical objective and force test."""
import unittest
from types import SimpleNamespace
import numpy as np
from physics.contact_events import ContactEventLimiter, FrontStripperEventProvider, limiter_from_config
from physics.bordered_newton import minimize_bordered


def prepared(gaps, speeds):
    return SimpleNamespace(gaps=lambda a: np.atleast_1d(gaps(a)),
                           speed_bounds=np.atleast_1d(speeds),
                           sample_ids=[('synthetic', i) for i in range(np.size(speeds))],
                           scope='synthetic signed gap oracle')


class ContactEvents(unittest.TestCase):
    def limit(self, gaps, speeds, **options):
        monitor = prepared(gaps, speeds)
        return ContactEventLimiter(lambda x, d: monitor, **options)(np.zeros(1), np.ones(1))

    def assert_event(self, result, target, kind='activation'):
        self.assertTrue(result['event_found'])
        self.assertTrue(result['verified_buffered_event'])
        self.assertTrue(result['search_complete'])
        self.assertEqual(result['event_kind'], kind)
        self.assertAlmostEqual(result['cap_gap_mm'], target, delta=1.25e-6)
        self.assertLessEqual(result['bracket_motion_bound_mm'], 1.25e-6)
        self.assertGreater(result['alpha'], 0.)

    def test_linear_activation_has_finite_verified_depth(self):
        result = self.limit(lambda a: .1-a, 1.)
        self.assert_event(result, -1e-5)
        self.assertGreater(result['alpha'], .1)
        self.assertLess(result['alpha'], .100012)

    def test_initial_exact_touch_does_not_create_zero_length_step(self):
        result = self.limit(lambda a: -a, 1.)
        self.assert_event(result, -1e-5)
        self.assertGreaterEqual(result['alpha'], 1e-5)

    def test_simultaneous_contacts_keep_stable_sample_identities(self):
        result = self.limit(lambda a: np.array([.1-a, .2-2*a, 1.]), [1., 2., 0.])
        self.assert_event(result, -1e-5)
        self.assertEqual(result['sample_id'], ['synthetic', 1])
        # Finite depth for the faster sample precedes the slower sample's depth.
        simultaneous = self.limit(lambda a: np.array([.1-a, .1-a]), [1., 1.])
        self.assertEqual(simultaneous['simultaneous_crossed_samples'], 2)

    def test_separation_and_recontact_use_opposite_finite_buffers(self):
        separation = self.limit(lambda a: -.1+a, 1.)
        self.assert_event(separation, 1e-5, 'separation')
        start_gap = separation['cap_gap_mm']
        recontact = self.limit(lambda a: start_gap-a, 1.)
        self.assert_event(recontact, -1e-5)
        self.assertGreater(recontact['alpha'], start_gap)

    def test_hidden_entry_then_exit_is_found_before_clear_endpoint(self):
        result = self.limit(lambda a: abs(a-.4)-.1, 1.)
        self.assert_event(result, -1e-5)
        self.assertLess(result['alpha'], .4)

    def test_closest_feature_change_preserves_distance_search(self):
        # Distance is continuous but switches closest feature at alpha=.25.
        result = self.limit(lambda a: min(.5-a, .3-.2*a), 1.)
        self.assert_event(result, -1e-5)
        self.assertGreater(result['alpha'], .5)

    def test_clear_step_is_certified_and_budget_failure_is_explicit(self):
        clear = self.limit(lambda a: .2+.1*a, .1)
        self.assertTrue(clear['search_complete'])
        self.assertFalse(clear['event_found'])
        self.assertEqual(clear['alpha'], 1.)
        limited = self.limit(lambda a: .1-a, 1., max_queries=2)
        self.assertFalse(limited['search_complete'])
        self.assertFalse(limited['event_found'])
        self.assertEqual(limited['alpha'], 1.)
        self.assertEqual(limited['fallback'], 'query_budget')

    def test_invalid_bound_and_nonfinite_gap_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'motion bound'):
            self.limit(lambda a: .1-2*a, .1)
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            self.limit(lambda a: np.nan, 1.)
        with self.assertRaises(ValueError):
            self.limit(lambda a: .1-a, -1.)

    def test_configuration_is_opt_in_and_rejects_unknown_scope(self):
        self.assertIsNone(limiter_from_config(None, None))
        self.assertIsNone(limiter_from_config(None, {'enabled': False}))
        for bad in [{'enabled': 1}, {'enabled': True, 'scope': 'all_contacts'},
                    {'enabled': False, 'invented': True}, ['enabled']]:
            with self.assertRaises(ValueError):
                limiter_from_config(None, bad)

    def test_budget_check_can_interrupt_before_more_queries(self):
        checks = []
        def budget():
            checks.append(1)
            if len(checks) == 3:
                raise TimeoutError('bounded_event_search')
        with self.assertRaisesRegex(TimeoutError, 'bounded_event_search'):
            self.limit(lambda a: .1-a, 1., budget_check=budget)
        self.assertEqual(len(checks), 3)

    def test_penalty_equilibrium_refreshes_curvature_without_weakening_force(self):
        def objective(x):
            return (.5*(x[0]+.1)**2+.5*x[1]**2+50*min(x[0], 0.)**2,
                    np.array([x[0]+.1+100*min(x[0], 0.), x[1]]))
        def monitor(x, d):
            return prepared(lambda a: x[0]+a*d[0], abs(d[0]))
        limiter = ContactEventLimiter(monitor)
        trace = []
        x, result = minimize_bordered(objective, np.array([.1, 0.]), 1,
                                      lambda x: True, maxiter=20, spectral='absolute_damped',
                                      callback=lambda x, info: trace.append(info),
                                      contact_event_limiter=limiter)
        self.assertTrue(result['optimizer_success'])
        self.assertLessEqual(abs(objective(x)[1]).max(), 1e-8)
        self.assertAlmostEqual(x[0], -.1/101., places=10)
        events = [r for r in trace if r['contact_event']['accepted_at_event_cap']]
        self.assertTrue(events)
        self.assertTrue(all(r['contact_event']['next_iteration_rebuilds_hessian'] for r in events))

    def test_event_cap_never_bypasses_original_path_guard(self):
        start = np.array([.1, 0.])
        def objective(x):
            return .5*np.dot(x+.1, x+.1), x+.1
        limiter = ContactEventLimiter(lambda x, d: prepared(lambda a: x[0]+a*d[0], abs(d[0])))
        x, result = minimize_bordered(objective, start, 1, lambda x: True, maxiter=2,
                                      step_admissible=lambda a, b: False,
                                      contact_event_limiter=limiter)
        np.testing.assert_array_equal(x, start)
        self.assertEqual(result['message'], 'line_search')
        self.assertFalse(result['optimizer_success'])

    def test_backtracking_before_cap_is_not_reported_as_accepted_event(self):
        def objective(x):
            return .5*np.dot(x, x), x.copy()
        report = {'alpha': 1., 'event_found': True, 'scope': 'test'}
        trace = []
        x, result = minimize_bordered(objective, np.array([1., 0.]), 1,
                                      lambda x: True, maxiter=1, max_step=2.,
                                      contact_event_limiter=lambda x, d: report,
                                      step_admissible=lambda a, b: np.linalg.norm(b-a) < .75,
                                      callback=lambda x, info: trace.append(info))
        self.assertFalse(trace[0]['contact_event']['accepted_at_event_cap'])
        self.assertEqual(trace[0]['contact_event']['accepted_alpha'], .5)
        self.assertAlmostEqual(x[0], .5, places=8)


class FrontStripperProvider(unittest.TestCase):
    def fixture(self):
        corners = [[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]]
        profile = {'profile_axes': [0, 1], 'extrusion_axis': 2,
                   'extrusion_bounds_mm': [-1., 1.], 'holes': [],
                   'outer': {'points': corners, 'analytic_features': [
                       {'kind': 'LINE', 'a': a, 'b': b}
                       for a, b in zip(corners, corners[1:]+corners[:1])]}}
        world = SimpleNamespace(origin=np.zeros(3), frame=np.eye(3),
                                local=SimpleNamespace(plates=True,
                                profiles={'R01_front_stripper': profile}))
        q = np.array([[2., -.5, 0.], [2., .5, 0.], [3., .5, 0.]])
        def unpack(x):
            actual = q.copy()
            actual[:2] = x[:6].reshape(-1, 3)
            return actual, None, None, None
        model = SimpleNamespace(obstacle=SimpleNamespace(base=SimpleNamespace(base=world)),
                                cfg={'yarn_radius_mm': .1}, free=np.array([0, 1]),
                                interior=6, fixed_indices=np.array([], dtype=int),
                                nip_grip=None, rest=np.array([1., 1.]), counts=np.array([8, 8]),
                                step_speed_bounds=lambda d: (np.array([]), 0.), unpack=unpack)
        return model, q[:2].ravel(), np.tile([-2., 0., 0.], 2)

    def test_swept_selection_includes_initially_distant_samples_without_mutation(self):
        model, x, d = self.fixture()
        counts, rest = model.counts.copy(), model.rest.copy()
        provider = FrontStripperEventProvider(model)
        monitor = provider(x, d)
        self.assertTrue(all(monitor.gaps(0.) > 0.))
        ids = monitor.sample_ids.copy()
        result = ContactEventLimiter(provider)(x, d)
        self.assertTrue(result['event_found'])
        self.assertEqual(result['sample_id'][:2], ['R01_front_stripper', 0])
        self.assertAlmostEqual(result['alpha'], .450005, delta=1e-6)
        self.assertEqual(ids, monitor.sample_ids)
        np.testing.assert_array_equal(model.counts, counts)
        np.testing.assert_array_equal(model.rest, rest)
        np.testing.assert_array_equal(monitor.reference_weights_mm,
                                      rest[[i[1] for i in ids]]/counts[[i[1] for i in ids]])
        # The exact signed-distance change stays inside the supplied bound.
        np.testing.assert_array_less(abs(monitor.gaps(.8)-monitor.gaps(.2)),
                                     .6*monitor.speed_bounds+1e-12)


if __name__ == '__main__':
    unittest.main()
