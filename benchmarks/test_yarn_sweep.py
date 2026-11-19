"""Regression cases for continuous segment clearance in millimetres."""
import unittest

import numpy as np

from examples.yarn_sweep import coil_example, evaluate, midpoint_bounds, narrow_interval


class YarnSweepTests(unittest.TestCase):
    def test_midstroke_overlap_survives_clear_endpoints(self):
        start = np.array([[-2., 0, 0], [2., 0, 0], [0, -2, 1], [0, 2, 1]])
        finish = start.copy()
        finish[2:, 2] = -1
        self.assertGreater(midpoint_bounds(start, 0.6)[0], 0)
        self.assertGreater(midpoint_bounds(finish, 0.6)[0], 0)
        _, finding = narrow_interval(start, finish, 0.6, 0.01, 10)
        self.assertEqual(finding["status"], "overlap")
        self.assertEqual(finding["time"], 0.5)

    def test_common_motion_cancels_in_the_time_bound(self):
        start = np.array([[0., 0, 0], [2., 0, 0], [0, 1, 0], [2, 1, 0]])
        lower, finding = narrow_interval(start, start + [80, 13, -5], 0.6, 0.01, 0)
        self.assertIsNone(finding)
        self.assertAlmostEqual(lower, 0.4, places=7)

    def test_subdivision_exhaustion_is_visible(self):
        start = np.array([[-1., 0, 0], [1., 0, 0], [0, -1, 0.61], [0, 1, 0.61]])
        finish = start.copy()
        finish[2:, 0] += 2
        _, finding = narrow_interval(start, finish, 0.6, 0.01, 0)
        self.assertEqual(finding["status"], "unresolved")

    def test_coincident_points_and_parallel_edges(self):
        self.assertEqual(midpoint_bounds(np.zeros((4, 3)), 0.6), (-0.6, -0.6))
        points = np.array([[0., 0, 0], [1., 0, 0], [0, 1, 0], [1, 1, 1.e-14]])
        low, high = midpoint_bounds(points, 0.6)
        self.assertLessEqual(low, high + 1e-13)
        self.assertAlmostEqual(low, 0.4)

    def test_nonfinite_input_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(np.full((2, 5, 3), np.nan), np.ones(4))

    def test_coil_against_analytical_axial_spacing(self):
        poses, rest = coil_example()
        np.testing.assert_allclose(poses[:, 64, 2], np.linspace(1.2, 2.2, 9))
        result = evaluate(poses, rest)
        self.assertTrue(result["passed"])
        self.assertEqual(result["intervals"], 8)
        self.assertGreater(result["worst"]["lower_mm"], 0)
