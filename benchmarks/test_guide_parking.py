"""Check the four separate tool travels and the parked yarn measurement."""
import unittest
from math import dist, inf, nan

from examples.closed_hook_return import command_at as first_draw
from examples.guide_parking import PHASES, command_at, parked_rim_gap, phase_segment, waypoints


class GuideParkingTests(unittest.TestCase):
    def test_continuous_separate_axis_distances(self):
        lengths = [17.245, 0.7934634170614636, 8.354545454545462, 0.259943181818187]
        last = first_draw(withdrawal_mm=0.48)
        for phase, length in zip(PHASES, lengths):
            start, end, axis = phase_segment(phase)
            self.assertEqual(start, last)
            actual = dist(start[axis], end[axis])
            self.assertAlmostEqual(actual, length, places=10)
            for fraction in [0., .25, .5, 1.]:
                command = command_at(phase, actual*fraction)
                self.assertEqual(command[1-axis], start[1-axis])
                self.assertAlmostEqual(dist(start[axis], command[axis]), actual*fraction, places=10)
                self.assertAlmostEqual(dist(command[axis], end[axis]), actual*(1-fraction), places=10)
            last = end
        self.assertLess(dist(last[0], (139.175731505,159.770532276,87.131681167)), 1e-8)
        self.assertLess(dist(last[1], (136.,190.,96.536749839)), 1e-8)

    def test_guide_axis_and_centering(self):
        points = waypoints()
        for i in (0,2):
            a,b = points[i][1],points[i+1][1]
            self.assertEqual(a[0], b[0])
            self.assertAlmostEqual((b[2]-a[2])/(b[1]-a[1]), 0.3639702342662, places=10)
        self.assertEqual(points[-2][1][1:], points[-1][1][1:])

    def test_parked_surface_gap(self):
        self.assertAlmostEqual(parked_rim_gap(), 0.3683689810492705, places=10)

    def test_invalid_phase_or_local_travel(self):
        for phase, travel in [('guide-center', -.1), ('hook-backoff', .9),
                              ('guide-finish', nan), ('guide-start', inf), ('other', 0)]:
            with self.subTest(phase=phase, travel=travel), self.assertRaises(ValueError):
                command_at(phase, travel)


if __name__ == '__main__':
    unittest.main()
