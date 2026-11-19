import unittest

import numpy as np

from examples.yarn_weight import comparison
from physics.loop_holding import rod_gravity


class YarnWeight(unittest.TestCase):
    def test_nonuniform_rod_against_native_force_and_energy(self):
        rest = np.array([10., 20., 30.])
        positions = np.array([[0., 0., 4.], [8., 0., 10.], [8., 12., 26.], [38., 12., 26.]])
        a = rod_gravity(positions, rest, 0.1)
        b = rod_gravity(positions, rest, 0.16)
        result = comparison(rest, 100., 160., [1, 2])
        delta = b[1] - a[1]
        np.testing.assert_allclose(result["nodal_weight_difference_N"], delta[:, 2], rtol=2e-15)
        self.assertAlmostEqual(b[0] - a[0], float((delta * positions).sum()), places=16)
        self.assertAlmostEqual(delta[:, 2].sum(), 60. * 60. * 9.80665e-9, places=18)
        self.assertEqual(result["governing_free_node"], 2)
        self.assertAlmostEqual(result["common_pose_lower_bound_N"], 7.3549875e-6, places=18)

    def test_bound_is_sharp_at_the_mean_load(self):
        result = comparison([10., 20., 30.], 160., 100., [0])
        self.assertAlmostEqual(result["common_pose_lower_bound_N"], 60. * 5. * 9.80665e-9 / 2)
        self.assertEqual(comparison([1.], 125., 125., [1])["common_pose_lower_bound_N"], 0.)

    def test_invalid_cases(self):
        for values in [([], 0, 1, [0]), ([0], 1, 2, [0]), ([1], -1, 2, [1]),
                       ([1], 1, float("nan"), [0]), ([1], 1, 2, []), ([1], 1, 2, [2])]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                comparison(*values)
