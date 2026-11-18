import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
from scipy.optimize import brentq

from physics.clamp_contact_events import MovingClampEventProvider, CombinedContactLimiter
from physics.contact_events import ContactEventLimiter
from physics.fixture_contact import ClampContact
from physics.rigid_clamp import rotation


def fixture_model(q, fixed=None):
    spec = json.loads((Path(__file__).resolve().parents[1]/'spec/r5_m2_fixture.json').read_text())['cloth_clamp']
    fixed_ids = np.array(fixed['indices'] if fixed else [], dtype=int)
    free = np.array([i for i in range(len(q)) if i not in fixed_ids], dtype=int)
    interior = 3*len(free)
    def unpack(x):
        actual = q.copy(); actual[free] = x[:interior].reshape(-1, 3)
        c, a = x[interior:interior+3], x[interior+3:interior+6]
        if fixed:
            R, _ = rotation(a, spec['angular_scale_mm'])
            actual[fixed_ids] = c+np.array(fixed['body_xyz_mm'])@R.T
        return actual, c, a, 0.
    rest = np.linalg.norm(np.diff(q, axis=0), axis=1)
    model = SimpleNamespace(clamp_spec=spec, fixed_section=fixed, fixed_indices=fixed_ids,
        angle_scale=spec['angular_scale_mm'], cfg={'yarn_radius_mm': .3}, free=free,
        interior=interior, rest=rest, counts=np.full(len(rest), 8), unpack=unpack)
    return model, np.r_[q[free].ravel(), np.zeros(6)]


class ClampContactEvents(unittest.TestCase):
    def test_first_activation_matches_independent_rotating_plane_solution(self):
        seed = np.array([[-20., 0., 3.], [-19., 0., 3.]])
        model, _ = fixture_model(seed)
        s = model.clamp_spec
        outer = s['closed_face_gap_mm']/2+s['pad_thickness_mm']+s['jaw_thickness_mm']
        seed[:, 1] = -outer-.3-.12
        model, x = fixture_model(seed)
        direction = np.r_[np.tile([.01, .4, 0.], 2), [.05, .1, 0.], [.02*model.angle_scale, 0., 0.]]
        provider = MovingClampEventProvider(model)
        monitor = provider(x, direction)
        result = ContactEventLimiter(provider, max_queries=2048)(x, direction)
        self.assertTrue(result['verified_buffered_event'])
        fractions = (np.arange(8)+.5)/8
        initial = (1-fractions[:, None])*seed[0]+fractions[:, None]*seed[1]
        def exact_plane_gap(alpha):
            relative = initial+alpha*(np.array([.01, .4, 0.])-np.array([.05, .1, 0.]))
            theta = .02*alpha
            local_y = -np.sin(theta)*relative[:, 0]+np.cos(theta)*relative[:, 1]
            return -outer-local_y-.3
        expected = brentq(lambda a: np.min(exact_plane_gap(a))+1e-5, 0., 1.)
        self.assertAlmostEqual(result['alpha'], expected, delta=3e-6)
        for alpha in [0., .2, .5, .8, 1.]:
            np.testing.assert_allclose(monitor.gaps(alpha), exact_plane_gap(alpha), atol=2e-13)
        for a, b in [(0., .2), (.2, .8), (.8, 1.)]:
            self.assertTrue(np.all(abs(monitor.gaps(b)-monitor.gaps(a)) <= (b-a)*monitor.speed_bounds+1e-12))
        np.testing.assert_array_equal(monitor.reference_weights_mm, np.full(8, model.rest[0]/8))
        np.testing.assert_array_equal(provider.body.center, np.zeros(3))

    def test_material_specific_grip_remains_clear_during_coupled_rigid_motion(self):
        q = np.array([[-7.95, 0., z] for z in [2.65, 3.35, 4.65, 5.35]])
        section = {'indices': [0, 1, 2, 3], 'body_xyz_mm': q.tolist(), 'gripped_edges': [0, 1, 2]}
        model, x = fixture_model(q, section)
        direction = np.array([1., -2., .5, 4., 7., -3.])
        provider = MovingClampEventProvider(model); monitor = provider(x, direction)
        np.testing.assert_array_equal(monitor.speed_bounds, np.zeros(len(monitor.sample_ids)))
        self.assertTrue(np.all(monitor.gaps(0.) > 0.))
        for alpha in [.1, .7, 1.]:
            np.testing.assert_allclose(monitor.gaps(alpha), monitor.gaps(0.), atol=1e-13)
        result = ContactEventLimiter(provider)(x, direction)
        self.assertFalse(result['event_found'])
        self.assertTrue(result['search_complete'])
        plain = ClampContact(model.clamp_spec, [0., 0., 0.], [0., 0., 0.])
        points = np.array([[-7.95, 0., 4.]])
        self.assertLess(plain.distance(points)[0][0], .3)
        self.assertGreater(provider.body.distance_for_edges(points, [1])[0][0], .3)

    def test_combination_retains_verified_cap_without_inventing_complete_coverage(self):
        class Fixed:
            def __init__(self, row): self.row = row
            def __call__(self, x, d): return self.row.copy()
        common = {'queries': 2, 'elapsed_s': .01, 'sample_count': 1, 'verified_buffered_event': False,
                  'event_found': False, 'search_complete': True, 'alpha': 1.}
        front = Fixed({**common, 'search_complete': False, 'fallback': 'query_budget'})
        clamp = Fixed({**common, 'alpha': .2, 'event_found': True,
                       'verified_buffered_event': True, 'sample_id': ['moving_clamp', 1, 2]})
        result = CombinedContactLimiter(front, clamp)(None, None)
        self.assertEqual(result['alpha'], .2)
        self.assertEqual(result['selected_monitor'], 'moving_clamp')
        self.assertTrue(result['verified_buffered_event'])
        self.assertFalse(result['earliest_across_monitors_proven'])
        self.assertFalse(result['search_complete'])


if __name__ == '__main__':
    unittest.main()
