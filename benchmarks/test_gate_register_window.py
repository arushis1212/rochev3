import unittest

from examples.gate_register_window import intervals


class GateRegisterWindowTest(unittest.TestCase):
    def test_corners_and_common_setting(self):
        settings = intervals()
        self.assertEqual(set(settings), {-.01,.02,.05})
        self.assertIsNone(settings[.02][1])
        common = (max(settings[h][0] for h in (-.01,.05)), min(settings[h][1] for h in (-.01,.05)))
        self.assertAlmostEqual(common[0], -.002943057658, places=10)
        self.assertAlmostEqual(common[1], .003334690568, places=10)
        self.assertLess(common[0], 0)
        self.assertGreater(common[1], 0)
