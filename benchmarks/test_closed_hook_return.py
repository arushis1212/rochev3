import json
from math import dist, inf, nan
import unittest
from examples.closed_hook_return import COMMAND, command_at, guide_at, hook_stop, nominal_clearances, read_path, stations, tip_at


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
        crest = guide_at(marks[3])
        self.assertLess(dist(crest, (136.375, start[1], start[2])), 1e-8)
        stop = hook_stop(json.loads(COMMAND.read_text()))
        mid = guide_at((marks[3] + stop)/2)
        self.assertLess(dist(mid, [(a+b)/2 for a, b in zip(crest, guide_at(stop))]), 1e-10)

    def test_selected_hook_stop_and_independent_guide(self):
        data = json.loads(COMMAND.read_text())
        self.assertEqual((data['inclination_deg'], data['roll_deg'], data['gate_travel_mm']), (30, 270, 0))
        stop = hook_stop(data)
        self.assertAlmostEqual(stop - stations(read_path())[3], 3.0605017515228345)
        h0, g0 = command_at(stop)
        self.assertLess(dist(h0, data['bight_release']['held_head_tip_mm']), 1e-10)
        for withdrawal in [0., .2, .43, .48, .7]:
            head, guide = command_at(withdrawal_mm=withdrawal)
            self.assertEqual(head, h0)
            self.assertAlmostEqual(dist(g0, guide), withdrawal, places=11)
            self.assertAlmostEqual(guide[0], g0[0])
        self.assertLess(dist(guide_at(stop, .48), (136.2599431818182, 165.94429604089018, 87.78118963374489)), 1e-10)
        for travel, withdraw in [(stop+.0001, 0.), (stop-.0001, .48), (stop, -.01), (stop, .7001), (nan, 0.), (stop, inf)]:
            with self.subTest(travel=travel, withdraw=withdraw), self.assertRaises(ValueError):
                command_at(travel, withdraw)

    def test_measure_clearances_from_local_geometry(self):
        data = json.loads(COMMAND.read_text())['bight_release']
        values = nominal_clearances()
        expected = data['simulation_at_nominal_stop']
        self.assertAlmostEqual(values['full_radius_sleeve_clearance_mm'], expected['full_radius_sleeve_clearance_mm'], places=10)
        self.assertAlmostEqual(values['foundation_yarn_surface_gap_mm'], expected['minimum_nonadjacent_yarn_surface_gap_mm'], places=10)
        self.assertAlmostEqual(values['positive_crossing_material_mm'], data['nominal_crossing_geometry']['positive_crossing_material_mm'])
        lo, hi = data['exposed_stop_window_mm']
        self.assertLess(lo, data['nominal_guide_withdrawal_mm'])
        self.assertGreater(hi, data['nominal_guide_withdrawal_mm'])
        self.assertTrue(all(value > .2 for value in data['continuous_bounds_in_stop_window'].values()))

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
