import unittest
from examples.receiver_wrist import DATA, intervals_for, replay


class WristClearance(unittest.TestCase):
    def test_whole_route(self):
        report = replay()
        self.assertEqual(report["checked_components"], 733)
        self.assertAlmostEqual(report["mark_path_length_mm"], 23.216262, places=5)
        self.assertGreater(report["minimum_swept_clearance_mm"], .0697)

    def test_released_mark_route(self):
        report = replay(DATA.parent / 'castoff/marked_wrist')
        self.assertEqual(report['checked_components'],733)
        self.assertAlmostEqual(report['mark_path_length_mm'],40.459609,places=5)
        self.assertGreater(report['minimum_swept_clearance_mm'],.0724)

    def test_two_aperture_route(self):
        from examples.aperture_route import DATA as folder, replay as crossings
        events=crossings(folder)
        self.assertEqual([v['loop'] for v in events],['L1','L0'])
        self.assertGreater(min(v['distance_to_material_centerline_mm'] for v in events),1.23)
        report=replay(folder)
        self.assertEqual(report['checked_components'],733)
        self.assertAlmostEqual(report['mark_path_length_mm'],54.699514,places=5)
        self.assertGreater(report['minimum_swept_clearance_mm'],.0179)

    def test_gap_in_verification(self):
        rows = [{"leg":0,"fractions":[0,.45]}, {"leg":0,"fractions":[.5,1]}]
        with self.assertRaises(ValueError):
            intervals_for(0,rows)


if __name__ == "__main__":
    unittest.main()
