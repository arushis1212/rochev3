import unittest
import numpy as np

from physics.compiled_clamp_distance import CompiledClampDistance
from physics.fixture_contact import ClampContact
from tests.test_clamp_contact_events import fixture_model


class CompiledClampDistanceTests(unittest.TestCase):
    def setUp(self):
        q = np.array([[-7.95, 0., z] for z in [2.65, 3.35, 4.65, 5.35]])
        section = {'indices': [0, 1, 2, 3], 'body_xyz_mm': q.tolist(), 'gripped_edges': [0, 1, 2]}
        model, _ = fixture_model(q, section)
        self.body = ClampContact(model.clamp_spec, [0., 0., 0.], [0., 0., 0.], section)
        self.fast = CompiledClampDistance(self.body)

    def compare(self, points, edges):
        reference = self.body.distance_for_edges(points, edges)[0]
        actual = self.fast.distances(points, self.fast.groups_for_edges(edges))
        np.testing.assert_allclose(actual, reference, rtol=0, atol=2e-12)

    def test_randomized_full_body_and_grip_neighborhoods_match_original_oracle(self):
        rng = np.random.default_rng(20261117)
        points = rng.uniform([-54., -9., -8.], [54., 13., 8.], (2000, 3))
        points = np.vstack([points, [-7.95, 0., 4.]+rng.uniform(-1., 1., (1000, 3))])
        edges = rng.choice([0, 1, 2, 99], len(points))
        self.compare(points, edges)

    def test_exact_box_corners_faces_and_cylinder_boundaries_match(self):
        points = []
        for lo, hi in self.body.rigid.boxes+self.body.pads.boxes:
            lo, hi = np.asarray(lo), np.asarray(hi)
            points.append((lo+hi)/2)
            points.extend(np.array([lo[0] if i == 0 else hi[0],
                                    lo[1] if j == 0 else hi[1],
                                    lo[2] if k == 0 else hi[2]])
                          for i in range(2) for j in range(2) for k in range(2))
        for origin, length, inner, outer in self.body.spacers:
            for radius in [inner, outer]:
                for yy in [-length/2, 0., length/2]:
                    points.extend(origin+[xx, yy, zz] for xx, zz in
                                  [(radius, 0.), (-radius, 0.), (0., radius), (0., -radius)])
        pin = self.body.spec['return_pin'];origin = np.asarray(pin['center_body_mm'])
        points.extend(origin+[pin['diameter_mm']/2, yy, 0.] for yy in
                      [-pin['length_mm']/2, 0., pin['length_mm']/2])
        points = np.asarray(points)
        for edge in [0, 1, 2, 99]:
            self.compare(points, np.full(len(points), edge))

    def test_invalid_material_groups_and_nonfinite_points_fail_closed(self):
        for points, groups in [(np.zeros((2, 3)), np.array([0, 99])),
                               (np.full((1, 3), np.nan), np.array([0])),
                               (np.zeros((1, 2)), np.array([0])),
                               (np.zeros((1, 3)), np.array([0.]))]:
            with self.assertRaises(ValueError): self.fast.distances(points, groups)


if __name__ == '__main__':
    unittest.main()
