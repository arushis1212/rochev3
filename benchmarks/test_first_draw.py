import unittest

import numpy as np

from examples.first_draw import HEEL, disk_crossings, replay, sections_stay_captured


class FirstDrawTests(unittest.TestCase):
    def test_registered_mark_history_and_retention(self):
        result = replay()
        self.assertEqual(result["motion_intervals"], 190)
        self.assertAlmostEqual(result["bight_rest_gain_mm"], 11.9529906058301)
        traces = result["fixed_mark_traces"]
        self.assertEqual([r["sign"] for r in traces["cloth_limb"]["events"]], [-1, 1, -1])
        self.assertEqual([r["sign"] for r in traces["supply_limb"]["events"]], [-1])
        self.assertTrue(all(row["net_oriented_crossings"] == -1 for row in traces.values()))
        self.assertGreater(min(row["final_whole_fiber_forward_margin_mm"] for row in traces.values()), .196)
        self.assertGreater(min(e["physical_rim_surface_gap_mm"] for row in traces.values() for e in row["events"]), 2.11)
        self.assertEqual(result["retained_through_all_five_pocket_sections"], {"old_heel": True, "working_nose": True})

    def test_reversing_temporal_motion_reverses_direction(self):
        points = np.array([[.25, .25, 1.], [.25, .25, -1.]])
        vertices = np.array([[0., 0., 0.], [2., 0., 0.], [0., 2., 0.]])
        for trajectory, expected in ((points, -1), (points[::-1], 1)):
            hits = disk_crossings(trajectory, vertices, np.array([[0, 1, 2]]), [0., 2.], .05)
            self.assertEqual([e['sign'] for e in hits], [expected])
            self.assertAlmostEqual(hits[0]['parameter_mm'], 1.)
        self.assertFalse(disk_crossings(points+[3., 0., 0.], vertices, np.array([[0, 1, 2]]), [0., 2.], .05))

    def test_heel_escape_is_detected(self):
        q = np.array([[-2., 0., 2.], [-2., 0., -2.]])
        self.assertTrue(sections_stay_captured(q, q, HEEL, -1))
        self.assertFalse(sections_stay_captured(q, q + [4.,0.,0.], HEEL, -1))


if __name__ == '__main__':
    unittest.main()
