import unittest
from examples.receiver_wrist import intervals_for, replay


class WristClearance(unittest.TestCase):
    def test_whole_route(self):
        report = replay()
        self.assertEqual(report["checked_components"], 733)
        self.assertAlmostEqual(report["mark_path_length_mm"], 23.216262, places=5)
        self.assertGreater(report["minimum_swept_clearance_mm"], .0697)

    def test_gap_in_verification(self):
        rows = [{"leg":0,"fractions":[0,.45]}, {"leg":0,"fractions":[.5,1]}]
        with self.assertRaises(ValueError):
            intervals_for(0,rows)


if __name__ == "__main__":
    unittest.main()
