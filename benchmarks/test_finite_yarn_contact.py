import unittest
import numpy as np
from physics.crossed_rod_contact import continuum
from physics.finite_yarn_contact import integrate


class FiniteContactTests(unittest.TestCase):
    def setUp(self):
        self.ends = np.array([[-1.2, 0., .33], [1.3, 0., .33], [-.1, 0., 0.], [.6, 1.1, 0.]])
        self.rest = [2.2, 1.4]

    def test_complete_footprint_at_oblique_angle(self):
        angle = .59
        direction = np.array([np.cos(angle), np.sin(angle), 0.])
        ends = np.array([[-3, 0, .49], [3, 0, .49], -3 * direction, 3 * direction])
        exact_energy, exact_force = continuum(.6, .49, 2.)
        # The material area per unit projected area includes stretch and angle.
        jacobian = 5.5 * 6.3 / (36 * np.sin(angle))
        energy, loads = integrate(ends, [5.5, 6.3], .6, 2., order=32)
        self.assertAlmostEqual(energy, exact_energy * jacobian, places=13)
        np.testing.assert_allclose(loads[:2].sum(axis=0), [0, 0, exact_force * jacobian], atol=1e-12)

    def test_end_clipping_and_energy_gradient(self):
        energy, loads = integrate(self.ends, self.rest, .6, 3., 36)
        self.assertGreater(energy, 0)
        for i, j in np.ndindex(4, 3):
            offset = np.zeros((4, 3))
            offset[i, j] = 1e-6
            lower = integrate(self.ends - offset, self.rest, .6, 3., 36)[0]
            upper = integrate(self.ends + offset, self.rest, .6, 3., 36)[0]
            self.assertAlmostEqual(loads[i, j], (lower - upper) / 2e-6, delta=2e-9)
        np.testing.assert_allclose(loads.sum(axis=0), 0., atol=1e-14)
        np.testing.assert_allclose(np.cross(self.ends, loads).sum(axis=0), 0., atol=1e-14)

    def test_swapping_and_exact_parallel_limit(self):
        for side in (0., .3, 1e-10):
            ends = np.array([[-.7, 0., .48], [1., 0., .48], [-.2, side, 0.], [1.2, 0., 0.]])
            energy, force = integrate(ends, self.rest, .6, 2., 40)
            perm = [3, 2, 0, 1]
            other, reversed_force = integrate(ends[perm], self.rest[::-1], .6, 2., 40)
            self.assertGreater(energy, 0.)
            self.assertAlmostEqual(other, energy, places=12)
            np.testing.assert_allclose(reversed_force, force[perm], atol=9e-12)

    def test_tiny_patch_and_no_contact(self):
        ends = np.array([[-35., 0., .59], [47., 0., .59], [2.345, -18., 0.], [2.345, 13., 0.]])
        exact_energy, exact_force = continuum(.6, .59, 1.)
        energy, force = integrate(ends, [82., 31.], .6, 1., 28)
        self.assertAlmostEqual(energy, exact_energy, delta=1e-15)
        self.assertAlmostEqual(force[:2, 2].sum(), exact_force, delta=2e-13)
        ends[:2, 2] = .61
        energy, loads = integrate(ends, [82., 31.], .6, 1.)
        self.assertEqual(energy, 0.)
        np.testing.assert_array_equal(loads, np.zeros((4, 3)))

    def test_inputs(self):
        for bad in (True, 3, 1000, 10.5):
            with self.assertRaises(ValueError):
                integrate(self.ends, self.rest, .6, 1., bad)
        with self.assertRaises(ValueError):
            integrate(self.ends, [0, 1], .6, 1.)
        with self.assertRaises(ValueError):
            integrate(self.ends[[0, 0, 2, 3]], self.rest, .6, 1.)
        with self.assertRaises(ValueError):
            integrate([[0., 0., 0.], [1., 0., 0.], [.3, 0., 0.], [.8, 0., 0.]], [1, 1], .6, 1.)
