from math import dist, nan
import unittest
from examples.closed_hook_return import read_path, stations, tip_at


class ReturnPathTests(unittest.TestCase):
    def test_machine_waypoints(self):
        path = read_path()
        marks = stations(path)
        self.assertEqual(len(path), 5)
        self.assertAlmostEqual(marks[-1], 13.962912023412057, places=9)
        for mark, point in zip(marks, path):
            self.assertLess(dist(tip_at(path, mark), point), 1e-10)

    def test_uniform_arc_length_within_each_segment(self):
        path = read_path()
        marks = stations(path)
        for i, (a, b) in enumerate(zip(marks, marks[1:])):
            p = tip_at(path, (a+b)/2)
            self.assertAlmostEqual(dist(p, path[i]), (b-a)/2, places=10)
            self.assertAlmostEqual(dist(p, path[i+1]), (b-a)/2, places=10)

    def test_reject_outside_or_degenerate_inputs(self):
        for s in (nan, -.00001, 14):
            with self.assertRaises(ValueError):
                tip_at(read_path(), s)
        for points in ([], [(0, 0, 0)]*2, [(0, 0), (1, 1)], [(0, 0, 0), (nan, 0, 0)]):
            with self.assertRaises(ValueError):
                stations(points)
