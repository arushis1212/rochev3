import unittest
from examples.gate_setting import predict

class GateSettingTests(unittest.TestCase):
    def test_both_loaded_and_changed_seating(self):
        seated=predict(0.,0.);open_gap=predict(.005,.005)
        self.assertAlmostEqual(seated["gate_bias_mm"],.0088272,places=7)
        self.assertAlmostEqual(open_gap["gate_bias_mm"],.0238116,places=7)
        self.assertAlmostEqual(seated["upper_normal_N"],1.3472,places=4)

    def test_unilateral_reactions_in_unbalanced_settings(self):
        for gaps in ((.014,0.),(0.,.014),(.014,.014)):
            r=predict(*gaps,tangent_ratio=-.20)
            for force,gap in zip(r["lower_normal_reactions_N"],r["remaining_lower_gaps_mm"]):
                self.assertGreaterEqual(force,-1e-10)
                self.assertGreaterEqual(gap,-1e-10)
                self.assertLess(abs(force*gap),1e-10)
            self.assertTrue(any(f==0 for f in r["lower_normal_reactions_N"]))

    def test_finite_studied_inputs(self):
        for args in ((.02,0.),(0.,0.,.4),(0.,0.,0.,float("nan"))):
            with self.assertRaises(ValueError):predict(*args)

    def test_shimmed_positions_replay_the_independent_force_extrema(self):
        cases = [("low_min", .170, -.006765762009, .011076726577),
                 ("mid", .266, -.006881232727, .011004375172),
                 ("high_max", .362, -.007000576179, .010930339133)]
        for pose, target, minimum, maximum in cases:
            results = [predict(x, y, mu, m, pose)["predicted_gate_opening_mm"]-target
                       for x in (0., .005) for y in (0., .005)
                       for mu in (-.05, .05) for m in (0., .370)]
            self.assertAlmostEqual(min(results), minimum, places=9)
            self.assertAlmostEqual(max(results), maximum, places=9)
        with self.assertRaises(ValueError):
            predict(0., .01, pose="low")
