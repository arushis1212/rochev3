import math
import unittest

from examples.hex_drive_fit import drive_budget


class HexDriveTests(unittest.TestCase):
    def test_aligned_axes_reduce_to_regular_hexagons(self):
        fit = drive_budget(2.55, 2.551, 0.010, 0, 0)
        self.assertEqual(fit.maximum_driver_mm, 2.55)
        self.assertAlmostEqual((2.551 - fit.minimum_driver_mm) / math.sqrt(3), 0.010)

    def test_direct_vertices_touch_the_enclosing_socket(self):
        # Project all six rotated tool vertices onto all six socket face normals.
        for angle in (0, 0.2, 10, 30):
            width = drive_budget(2.55, 2.55, 0.010, 0, 0, clock_deg=angle).maximum_driver_mm
            radius = width / math.sqrt(3)
            projections = [radius * math.cos(math.radians(30 + 60 * vertex + angle - 60 * face))
                           for vertex in range(6) for face in range(6)]
            self.assertAlmostEqual(max(projections), 2.55 / 2)

    def test_gauged_drive_interval(self):
        fit = drive_budget(2.550, 2.551, 0.010, 0.0005, 1.435, 0.2, 0.15)
        self.assertAlmostEqual(fit.minimum_driver_mm, 2.534545517328096, places=12)
        self.assertAlmostEqual(fit.maximum_driver_mm, 2.536360084012078, places=12)
        self.assertLess(fit.minimum_driver_mm, 2.535)
        self.assertLess(2.536, fit.maximum_driver_mm)

    def test_more_tilt_or_reach_reduces_entry_allowance(self):
        baseline = drive_budget(2.55, 2.551, 0.01, 0.0005, 1.435, 0.2, 0.15)
        for reach, tilt in [(1.6, 0.15), (1.435, 0.3)]:
            revised = drive_budget(2.55, 2.551, 0.01, 0.0005, reach, 0.2, tilt)
            self.assertLess(revised.maximum_driver_mm, baseline.maximum_driver_mm)

    def test_invalid_dimensions_and_angles(self):
        for args in [(2.55, 2.5, 0.01, 0, 1, 0, 0), (2, 3, 1, 0, 1, 31, 0),
                     (2, 3, 1, 0, 1, 0, 90), (2, 3, 1, 0, math.nan, 0, 0)]:
            with self.assertRaises(ValueError):
                drive_budget(*args)


if __name__ == '__main__':
    unittest.main()
