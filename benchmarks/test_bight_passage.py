import math
import unittest

from examples.bight_passage import passage, through_sleeve


def sample(height, offset=(0., 0.)):
    return passage(2., 15., 6., .6, .25, height, offset)


class BightPassageTests(unittest.TestCase):
    def test_finite_faces_and_yarn_radius(self):
        for height, expected in [(-1.5, False), (-1.25, False), (-1., True), (14.25, False)]:
            with self.subTest(height=height):
                result = through_sleeve(2., 15., 6., .25, height, 1.)
                self.assertEqual(result['both_legs_through_with_clearance'], expected)
        result = through_sleeve(2., 15., 6., .25, -1., 1.)
        self.assertAlmostEqual(result['tip_above_far_face_mm'], .25)
        self.assertAlmostEqual(result['sidewall_clearance_lower_mm'], 3.75)

    def test_finite_bore_offset(self):
        result = through_sleeve(2., 15., 6., .25, -1., 1., offset=(4., 0.))
        self.assertFalse(result['both_legs_through_with_clearance'])
        with self.assertRaises(ValueError):
            through_sleeve(2., 15., 6., .25, -1., float('nan'))

    def test_before_and_at_birth(self):
        for height in (-3., -2.):
            result = sample(height)
            self.assertEqual(result.length_beyond_plane_mm, 0.)
            self.assertEqual(result.crossings, ())

    def test_analytic_half_radius(self):
        result = sample(-1.)
        self.assertAlmostEqual(result.length_beyond_plane_mm, 4 * math.pi / 3)
        self.assertEqual(len(result.crossings), 2)
        for point, x, sign in zip(result.crossings, [-math.sqrt(3), math.sqrt(3)], [1, -1]):
            self.assertAlmostEqual(point[0], x)
            self.assertEqual(point[2], sign)

    def test_material_length_and_endpoints(self):
        for height in [0., 4., 14.999, 15., 16.]:
            result = sample(height)
            self.assertAlmostEqual(result.length_beyond_plane_mm, 2 * math.pi + 2 * min(height, 15.))
            self.assertEqual(len(result.crossings), 2 if height < 15. else 0)

    def test_ring_gap_against_actual_leg_witness(self):
        result = sample(1., (-1., 2.))
        self.assertAlmostEqual(result.ring_surface_gap_lower_mm,
                               6. - math.hypot(-3., 2.) - .6 - .25)
        for x, y, _ in result.crossings:
            self.assertGreaterEqual(6. - math.hypot(x, y) - .85 + 1e-14,
                                    result.ring_surface_gap_lower_mm)

    def test_only_passages_inside_ring_count(self):
        result = sample(0., (5., 0.))
        self.assertEqual(result.crossings, ((3., 0., 1),))
        self.assertLess(result.ring_surface_gap_lower_mm, 0.)

    def test_invalid_shapes(self):
        with self.assertRaises(ValueError):
            sample(float("nan"))
        with self.assertRaises(ValueError):
            passage(1, 3, 2, 2, .25, 0)
