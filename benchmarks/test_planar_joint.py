import itertools
import math
import unittest

from examples.planar_joint import Footprint, JointLoad, bounds, traction


class PlanarJointTests(unittest.TestCase):
    def test_rectangle_integrates_all_six_resultants(self):
        width, height = 7., 11.
        area = width * height
        foot = Footprint(area, area*width**2/12, 0., area*height**2/12)
        load = JointLoad(94., 13., -27., .8, 1.9, 6.)
        total = [0.]*6
        for iy, iz in itertools.product((-1., 1.), repeat=2):
            y = iy*width/(2*math.sqrt(3.))
            z = iz*height/(2*math.sqrt(3.))
            p, sy, sz = traction(foot, load, y, z)
            for i, value in enumerate((p, y*p, z*p, sy, sz, y*sz-z*sy)):
                total[i] += value*area/4
        for actual, expected in zip(total, (94., 13., -27., .8, 1.9, 6.)):
            self.assertAlmostEqual(actual, expected)

    def test_skew_moments(self):
        foot = Footprint(7., 13., -5., 17.)
        # With this moment pair, the recovered pressure gradient is (2, -1).
        load = JointLoad(14., 31., -27., 0., 0., 0.)
        self.assertAlmostEqual(traction(foot, load, .7, -.2)[0], 3.6)

    def test_interior_cone_and_lift(self):
        foot = Footprint(4., 4/3, 0., 4/3)
        load = JointLoad(10., -.25, .75, 1., 2., -3.)
        pmin, pmax, mu = bounds(foot, load, (-1., 1.), (-1., 1.))
        for i, j in itertools.product(range(-5, 6), repeat=2):
            p, sy, sz = traction(foot, load, i/5, j/5)
            self.assertGreaterEqual(p, pmin)
            self.assertLessEqual(p, pmax)
            self.assertLessEqual(math.hypot(sy, sz), mu*p+1e-14)
        pmin, _, mu = bounds(foot, JointLoad(4., 0., 2., 1., 0., 0.), (-1., 1.), (-1., 1.))
        self.assertLess(pmin, 0.)
        self.assertIsNone(mu)

    def test_invalid_geometry_or_load(self):
        with self.assertRaises(ValueError):
            Footprint(1., 1., 2., 4.)
        with self.assertRaises(ValueError):
            JointLoad(1., 0., float("nan"), 0., 0., 0.)
