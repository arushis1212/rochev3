import json
from pathlib import Path
import unittest

from examples.receiver_jaw import evaluate


class ReceiverJaw(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inputs = Path(__file__).resolve().parents[1] / "examples" / "receiver_jaw.json"
        cls.result = evaluate(json.loads(inputs.read_text()))

    def test_closing_nose_reaches_the_registered_strand(self):
        for event in self.result["closures"]:
            self.assertGreater(event["initial_gap_mm"], .6)
            self.assertAlmostEqual(event["final_gap_mm"], 0., places=7)
            self.assertGreater(event["final_normal_N"], .020)

    def test_the_same_yarn_mark_bears_on_the_nose(self):
        rows = self.result["draws"]
        self.assertGreaterEqual(len(rows), 15)
        self.assertAlmostEqual(rows[-1]["route_mm"], 24.3692762664)
        for state in rows:
            self.assertLess(abs(state["skin_mm"]), 1e-7)
            self.assertLess(abs(state["mark_error_mm"]), 1e-7)

    def test_both_contact_forces_fit_the_assumed_friction_cone(self):
        for state in self.result["draws"]:
            self.assertGreaterEqual(min(state["compressive_N"]), -1e-12)
            self.assertGreaterEqual(min(state["friction_slack_N"]), -1e-9)
            self.assertLess(state["input_torque_Nmm"], .1)

    def test_mobile_fabric_has_both_signed_limb_crossings(self):
        from examples.threaded_bight import measure
        path = Path(__file__).resolve().parents[1] / "examples" / "mobile_held_loops.npz"
        result = measure(path)
        self.assertAlmostEqual(result["eye_center_material_mm"], 1076.9507282, places=6)
        for loop in result["loops"].values():
            self.assertTrue(loop["two_limbs"])
            self.assertEqual(loop["signs"], [1, -1])
