import unittest
import numpy as np

from physics.full_stitch_aperture import MaterialAperture
from physics.full_stitch_aperture_sweep import certify_affine_aperture, _quadratic_bounds


class ApertureSweepTests(unittest.TestCase):
    def make(self, path=None, boundary=None):
        if boundary is None:
            boundary = [[-2., -2., 0.], [2., -2., 0.], [2., 2., 0.], [-2., 2., 0.]]
        if path is None:
            path = [[0., 0., -1.], [0., 0., 1.]]
        q = np.array([*boundary, *path], float)
        s = np.arange(len(q), dtype=float)
        ap = MaterialAperture.bind(q, s, [0, len(boundary)-1], [0, 0, 1])
        return ap, q, s, [len(boundary), len(q)-1]

    def check(self, ap, a, b, s, passing, **kw):
        return certify_affine_aperture(ap, a, b, s, passing,
            physical_margin_mm=.4, closure_margin_mm=.4, **kw)

    def test_static_crossing_disk_and_common_translation(self):
        ap, q, s, passing = self.make()
        a = self.check(ap, q, q, s, passing)
        b = self.check(ap, q, q+[40., -30., 20.], s, passing)
        self.assertTrue(a['certified'])
        self.assertTrue(b['certified'])
        self.assertEqual(b['evaluations'], 1)
        self.assertAlmostEqual(a['accepted_leaves'][0]['physical_boundary_lower_mm'],
                               b['accepted_leaves'][0]['physical_boundary_lower_mm'])
        self.assertFalse(b['physical_custody_certified'])
        self.assertFalse(b['passage_event_history_certified'])

    def test_nonplanar_affine_disk_is_accepted(self):
        ap, q, s, passing = self.make()
        q1 = q.copy()
        q1[:4, 2] = [0., .4, 0., -.3]
        self.assertTrue(self.check(ap, q, q1, s, passing)['certified'])

    def test_endpoint_clearance_cannot_hide_virtual_neck_crossing(self):
        ap, q, s, passing = self.make(path=[[-3., 0., -1.], [-3., 0., 1.]])
        q1 = q.copy()
        q1[-2:, 0] = 0.
        self.assertTrue(self.check(ap, q, q, s, passing)['certified'])
        self.assertTrue(self.check(ap, q1, q1, s, passing)['certified'])
        result = self.check(ap, q, q1, s, passing, max_depth=7)
        self.assertFalse(result['certified'])
        self.assertEqual(result['unresolved']['reason'], 'virtual_neck_separation')

    def test_endpoint_clearance_cannot_hide_physical_boundary_crossing(self):
        ap, q, s, passing = self.make(path=[[3., 0., -1.], [3., 0., 1.]])
        q1 = q.copy()
        q1[-2:, 0] = 0.
        result = self.check(ap, q, q1, s, passing, max_depth=7)
        self.assertFalse(result['certified'])
        self.assertEqual(result['unresolved']['reason'], 'physical_boundary_separation')

    def test_midpath_collapse_rejected_with_valid_endpoints(self):
        ap, q, s, passing = self.make()
        q1 = q.copy()
        q1[:4, :2] *= -1
        self.assertTrue(self.check(ap, q1, q1, s, passing)['certified'])
        result = self.check(ap, q, q1, s, passing, max_depth=5)
        self.assertFalse(result['certified'])

    def test_straight_boundary_vertices_remain_part_of_disk(self):
        ap, q, s, passing = self.make(boundary=[[-2, -2, 0], [0, -2, 0],
            [2, -2, 0], [2, 2, 0], [-2, 2, 0]])
        self.assertTrue(self.check(ap, q, q, s, passing)['certified'])
        q1 = q.copy()
        q1[1, 2] = .3
        self.assertTrue(self.check(ap, q, q1, s, passing)['certified'])

    def test_no_material_overlap_or_remesh_shortcut(self):
        ap, q, s, passing = self.make()
        with self.assertRaises(ValueError):
            self.check(ap, q, q, s, [2, 5])
        q2 = np.insert(q, 1, (q[0]+q[1])/2, axis=0)
        s2 = np.insert(s, 1, .5)
        q3 = q2.copy()
        q3[1, 2] = .1
        with self.assertRaises(ValueError):
            self.check(ap, q2, q3, s2, passing)

    def test_deadline_is_propagated_and_inputs_unchanged(self):
        ap, q, s, passing = self.make()
        original = q.copy()
        def deadline():
            raise TimeoutError('budget')
        with self.assertRaises(TimeoutError):
            self.check(ap, q, q, s, passing, deadline_check=deadline)
        np.testing.assert_array_equal(original, q)

    def test_point_segment_query_retains_clearance_and_no_mechanics_credit(self):
        ap, q, s, passing = self.make()
        q[-1] = q[-2]
        # The geometry of a point is well defined; rod strain is a separate gate.
        self.assertTrue(self.check(ap, q, q, s, passing, max_depth=0)['certified'])
        q[-2:] = [-2., 0., 0.]
        self.assertFalse(self.check(ap, q, q, s, passing, max_depth=0)['certified'])
        for depth in (-1, 1.2, True, 21):
            with self.assertRaises(ValueError):
                self.check(ap, q, q, s, passing, max_depth=depth)

    def test_quadratic_interior_minimum_not_only_endpoints(self):
        lo, hi = _quadratic_bounds(np.array([-.1]), np.array([0.]), np.array([1.]), 1.)
        self.assertLess(lo[0], -.1)
        self.assertGreater(hi[0], .9)

    def test_extreme_aspect_ratio_collapse_rejected(self):
        L, t = 1e10+.1, .2
        q0 = np.array([[0, 0, 0], [L, -t, 0], [2*L+t, -2*t, 0],
                       [0, 1000, 1000], [0, 1000, 1001]], float)
        q1 = np.array([[0, 0, 0], [L, 1-t, 0], [2*L-(1-t), 2*(1-t), 0],
                       [0, 1000, 1000], [0, 1000, 1001]], float)
        s = np.arange(5.)
        ap = MaterialAperture.bind(q0, s, [0, 2], [0, 0, 1], minimum_double_area=1e-12)
        result = self.check(ap, q0, q1, s, [3, 4], max_depth=0)
        self.assertFalse(result['certified'])
        self.assertEqual(result['unresolved']['reason'], 'projected_triangle_orientation')

    def test_sub_roundoff_clipped_segment_is_not_silently_removed(self):
        ap, q, s, passing = self.make(path=[[0, 0, -1], [0, 0, -1+1e-13], [0, 0, 1]])
        self.assertTrue(self.check(ap, q, q, s, passing)['certified'])
        q1 = q.copy()
        q1[-3:] += [-3., 0, 0]
        self.assertFalse(self.check(ap, q, q1, s, passing, max_depth=6)['certified'])

    def test_alternative_projection_handles_embedded_fold_without_retriangulation(self):
        ap, q, s, passing = self.make(path=[[100, 100, -1], [100, 100, 1]])
        q[:4] = [[-.9, -1, 0], [0, 0, 0], [-100, 0, 0], [0, 0, 1]]
        faces = q[ap.triangles]
        normals = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
        self.assertLess(float((normals@normals.sum(axis=0)).min()), 0.)
        before = ap.triangles.copy()
        result = self.check(ap, q, q, s, passing, max_depth=0)
        self.assertTrue(result['certified'])
        self.assertGreater(result['evaluations'], 1)
        np.testing.assert_array_equal(before, ap.triangles)


if __name__ == '__main__':
    unittest.main()
