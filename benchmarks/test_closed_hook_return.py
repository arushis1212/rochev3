from math import dist, nan
import unittest
from examples.closed_hook_return import guide_at, read_path, stations, tip_at


class ReturnPathTests(unittest.TestCase):
    def test_machine_waypoints(self):
        path = read_path()
        marks = stations(path)
        self.assertEqual(len(path), 5)
        self.assertAlmostEqual(marks[-1], 13.962912023412057, places=9)
        for mark, point in zip(marks, path):
            self.assertLess(dist(tip_at(path, mark), point), 1e-10)

    def test_linked_guide(self):
        marks = stations(read_path())
        self.assertEqual(guide_at(0), guide_at(marks[1]))
        mid = guide_at((marks[1] + marks[2])/2)
        start, end = guide_at(marks[1]), guide_at(marks[2])
        self.assertLess(dist(mid, [(a+b)/2 for a, b in zip(start, end)]), 1e-10)
        self.assertAlmostEqual(end[0] - start[0], 0.5625)
        with self.assertRaises(ValueError):
            guide_at(marks[3] + 0.001)
        crest = guide_at(marks[3])
        self.assertLess(dist(crest, (136.375, start[1], start[2])), 1e-8)

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
