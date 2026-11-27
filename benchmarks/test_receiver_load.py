import unittest
from pathlib import Path
from examples.receiver_load import replay


class SeatedReceiverTests(unittest.TestCase):
    def test_registered_static_contact(self):
        result=replay()
        self.assertEqual(result['free_nodes'],122)
        self.assertAlmostEqual(result['gate_opening_mm'],2.060672)
        self.assertLess(abs(result['needle_skin_gap_mm']),1e-7)
        self.assertLess(result['free_force_residual_nN'],.1)
        self.assertAlmostEqual(result['needle_force_mN'],3.226739,places=5)
        self.assertAlmostEqual(result['hook_body_force_mN'],82.044840,places=5)
        self.assertLess(result['main_gate_force_mN'],1e-6)

    def test_guide_advance_load(self):
        data=Path(__file__).resolve().parents[1]/"examples/receiver_load_guide.npz"
        r=replay(data)
        self.assertAlmostEqual(r["needle_force_mN"],7.167172,places=5)
        self.assertLess(r["free_force_residual_nN"],.1)
        self.assertLess(abs(r["needle_skin_gap_mm"]),1e-7)
