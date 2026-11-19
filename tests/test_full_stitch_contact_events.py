from types import SimpleNamespace
import unittest

import numpy as np

from physics.contact_events import ContactEventLimiter
from physics.full_stitch_contact_events import AnalyticalComponentEventProvider
from physics.rigid_clamp import rotation


class Sphere:
    def __init__(self, center, radius=1.):
        self.radius = radius
        self.center = np.array(center, float)
        self.update()

    def update(self):
        self.lo, self.hi = self.center-self.radius, self.center+self.radius

    def distance(self, p):
        relative = p-self.center
        norm = np.linalg.norm(relative, axis=1)
        return norm-self.radius, relative/np.maximum(norm[:, None], 1e-30)


def fixture(q, fixed=(), nip=(), extra=None):
    q = np.array(q, float)
    fixed, nip = np.array(fixed, int), np.array(nip, int)
    free = np.array([i for i in range(len(q)) if i not in set(fixed) | set(nip)], int)
    interior = 3*len(free)
    pulley = Sphere([0, 0, -2.])
    world = {'pulley_moving': pulley, **(extra or {})}
    model = SimpleNamespace(q=q, free=free, interior=interior, fixed_indices=fixed,
        rest=np.linalg.norm(np.diff(q, axis=0), axis=1), counts=np.full(len(q)-1, 4),
        cfg={'yarn_radius_mm': .3})
    scene = SimpleNamespace(world_obstacle=SimpleNamespace(components=world),
        obstacle=SimpleNamespace(components={**world, 'tail_clamp': object()}),
        moving_pulley=pulley, dynamic_component_contract={
            'other_dynamic_analytical_components': [],
            'pulley_moving': {'coordinates': 'feeder z', 'object_identity_count': 1}})
    model.contacts = scene
    def unpack(x):
        actual = q.copy()
        actual[free] = x[:interior].reshape(-1, 3)
        c, a = x[interior:interior+3], x[interior+3:interior+6]
        R, _ = rotation(a, 1.)
        actual[fixed] = c+q[fixed]@R.T
        return actual, c, a, x[-1]
    def pose(x):
        pulley.center[2] = x[-1]
        pulley.update()
        model.pose = x.copy()
    def speed(d):
        return (np.linalg.norm(d[interior:interior+3])+np.linalg.norm(q[fixed], axis=1)*sum(abs(d[interior+3:interior+6])),
                abs(d[-1]))
    model.unpack, model.set_obstacle_pose, model.step_speed_bounds = unpack, pose, speed
    x = np.r_[q[free].ravel(), np.zeros(6), -2.]
    pose(x)
    return model, x


class FullStitchContactEvents(unittest.TestCase):
    def test_hidden_midstep_activation_and_separation(self):
        model, x = fixture([[-.05, 0, 0], [.05, 0, 0]])
        d = np.zeros_like(x); d[-1] = 4.
        provider = AnalyticalComponentEventProvider(model, ['pulley_moving'])
        prepared = provider(x, d)
        self.assertTrue(np.all(prepared.gaps(0.) > 0.))
        self.assertTrue(np.all(prepared.gaps(1.) > 0.))
        self.assertTrue(np.all(prepared.gaps(.5) < 0.))
        result = ContactEventLimiter(provider, max_queries=2048)(x, d)
        expected = (2-np.sqrt((1.3-1e-5)**2-.0125**2))/4
        self.assertTrue(result['verified_buffered_event'])
        self.assertEqual(result['event_kind'], 'activation')
        self.assertAlmostEqual(result['alpha'], expected, delta=1e-6)
        np.testing.assert_array_equal(model.pose, x)
        x[-1] = .5; d[-1] = 1.
        result = ContactEventLimiter(provider, max_queries=2048)(x, d)
        self.assertTrue(result['verified_buffered_event'])
        self.assertEqual(result['event_kind'], 'separation')

    def test_fast_material_motion_and_reference_quadrature(self):
        model, x = fixture([[-.05, 0, 8], [.05, 0, 8]])
        d = np.zeros_like(x); d[:6] = np.tile([0, 0, -12.], 2)
        prepared = AnalyticalComponentEventProvider(model, ['pulley_moving'])(x, d)
        self.assertEqual(prepared.sample_ids, [('pulley_moving', 0, i) for i in range(4)])
        np.testing.assert_array_equal(prepared.reference_weights_mm, np.full(4, .025))
        np.testing.assert_array_equal(prepared.speed_bounds, np.full(4, 12.))
        for a, b in [(0., .3), (.3, .9), (.9, 1.)]:
            self.assertTrue(np.all(abs(prepared.gaps(b)-prepared.gaps(a)) <= (b-a)*prepared.speed_bounds+1e-12))

    def test_rotating_real_tail_and_world_fixed_inlet_bounds(self):
        model, x = fixture([[1., 0, 0], [.5, 0, 0], [0, 0, 0]], fixed=[0], nip=[2])
        d = np.zeros_like(x); d[model.interior:model.interior+3] = [.1, .2, .3]
        d[model.interior+3:model.interior+6] = [.7, -.2, .4]; d[-1] = 2.
        prepared = AnalyticalComponentEventProvider(model, ['pulley_moving'])(x, d)
        self.assertEqual(len(prepared.sample_ids), 8)
        for a, b in [(0., .2), (.2, .7), (.7, 1.)]:
            self.assertTrue(np.all(abs(prepared.gaps(b)-prepared.gaps(a)) <= (b-a)*prepared.speed_bounds+1e-12))
        np.testing.assert_array_equal(prepared.speed_bounds[4:], np.full(4, 2.))

    def test_distinct_body_events_and_original_edge_specific_grips(self):
        class Edged(Sphere):
            def distance_for_edges(self, p, edge_ids):
                self.last_edges = np.array(edge_ids)
                values, normals = self.distance(p)
                return values+np.where(np.asarray(edge_ids) == 0, 5., 0.), normals
        reduced = Edged([0., 0., 0.])
        model, x = fixture([[-.1, 0, 0], [0, 0, 0], [.1, 0, 0]], extra={'pad': reduced})
        d = np.zeros_like(x)
        prepared = AnalyticalComponentEventProvider(model, ['pad', 'pulley_moving'])(x, d)
        gap = prepared.gaps(0.)
        self.assertTrue(np.all(gap[:4] > 0.))
        self.assertTrue(np.all(gap[4:8] < 0.))
        np.testing.assert_array_equal(reduced.last_edges, [0]*4+[1]*4)
        self.assertEqual(len(set(prepared.sample_ids)), len(prepared.sample_ids))

    def test_pose_restored_even_when_distance_raises(self):
        model, x = fixture([[-.05, 0, 0], [.05, 0, 0]])
        d = np.zeros_like(x); d[-1] = 4.
        prepared = AnalyticalComponentEventProvider(model, ['pulley_moving'])(x, d)
        def fail(p): raise RuntimeError('distance failure')
        model.contacts.moving_pulley.distance = fail
        with self.assertRaises(RuntimeError): prepared.gaps(.5)
        np.testing.assert_array_equal(model.pose, x)

    def test_empty_selection_samples_and_invalid_contract_inputs(self):
        model, x = fixture([[100., 0, 0], [101., 0, 0]])
        provider = AnalyticalComponentEventProvider(model, ['pulley_moving'])
        prepared = provider(x, np.zeros_like(x))
        self.assertEqual(prepared.gaps(.5).shape, (0,))
        for alpha in [True, np.nan, -.1, 1.1]:
            with self.assertRaises(ValueError): prepared.gaps(alpha)
        for names in [[], ['unknown'], ['tail_clamp'], ['pulley_moving']*2]:
            with self.assertRaises(ValueError): AnalyticalComponentEventProvider(model, names)
        d = np.zeros_like(x); d[0] = np.inf
        with self.assertRaises(ValueError): provider(x, d)
        model.contacts.dynamic_component_contract['other_dynamic_analytical_components'] = ['unexpected']
        with self.assertRaises(ValueError): AnalyticalComponentEventProvider(model, ['pulley_moving'])


if __name__ == '__main__':
    unittest.main()
