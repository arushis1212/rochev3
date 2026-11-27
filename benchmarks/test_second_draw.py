from pathlib import Path
import unittest

from examples.receiver_load import replay


class SecondDrawTests(unittest.TestCase):
    def test_secondary_gate_and_original_needle_share_load(self):
        data = Path(__file__).resolve().parents[1] / 'examples' / 'second_draw_210.npz'
        result = replay(data)
        self.assertGreater(result['free_nodes'], 100)
        self.assertLess(result['free_force_residual_nN'], .1)
        self.assertLess(abs(result['needle_skin_gap_mm']), 1e-7)
        self.assertAlmostEqual(result['secondary_gate_force_mN'], 6.12023, places=4)
        self.assertAlmostEqual(result['needle_force_mN'], 1.52705, places=4)
