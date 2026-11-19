import math
import unittest

from examples.wheel_wrap import chord_loss_mm, segment_count


class CircularTrajectoryTests(unittest.TestCase):
    def test_exact_midpoint_of_chord(self):
        angle = math.pi / 3
        a = (12., 0.)
        b = (12.*math.cos(angle), 12.*math.sin(angle))
        midpoint_radius = math.hypot((a[0]+b[0])/2, (a[1]+b[1])/2)
        self.assertAlmostEqual(chord_loss_mm(12., angle), 12.-midpoint_radius)
        self.assertEqual(chord_loss_mm(12., angle), chord_loss_mm(12., -angle))

    def test_positive_minimal_count(self):
        for turn in (.01, math.pi/3, math.pi, 2*math.pi, 3*math.pi):
            for tolerance in (1e-6, .02, 2., 100.):
                n = segment_count(12., turn, tolerance)
                self.assertLessEqual(turn/n, math.pi)
                self.assertLessEqual(chord_loss_mm(12., turn/n), tolerance)
                if n > 1 and turn/(n-1) <= math.pi:
                    self.assertGreater(chord_loss_mm(12., turn/(n-1)), tolerance)

    def test_exact_zero_and_semicircle(self):
        self.assertEqual(segment_count(12., 0., .02), 1)
        self.assertEqual(segment_count(12., math.pi, 13.), 1)
        self.assertAlmostEqual(chord_loss_mm(12., math.pi), 12.)

    def test_very_small_angle(self):
        angle = 1e-8
        self.assertAlmostEqual(chord_loss_mm(12., angle)/(angle**2), 12./8, places=14)

    def test_domain(self):
        for radius, angle, tol in [(0., 1., .1), (2., math.inf, .1), (2., 1., 0.), (math.nan, 1., .1)]:
            with self.assertRaises(ValueError):
                segment_count(radius, angle, tol)
        with self.assertRaises(ValueError):
            chord_loss_mm(12., 4.)
