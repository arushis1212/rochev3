import unittest
from pathlib import Path

from examples.draw_feeder import replay as meter
from examples.receiver_load import replay as balance
from examples.threaded_bight import measure


EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


class DownstreamDrawTests(unittest.TestCase):
    def test_transfer_of_load_at_fixed_downstream_pose(self):
        touch = balance(EXAMPLES / 'downstream_touch.npz')
        released = balance(EXAMPLES / 'downstream_released.npz')
        self.assertAlmostEqual(touch['secondary_gate_force_mN'], 6.10848, places=4)
        self.assertAlmostEqual(touch['downstream_eye_force_mN'], .200881, places=5)
        self.assertAlmostEqual(released['secondary_gate_force_mN'], 0., places=7)
        self.assertAlmostEqual(released['downstream_eye_force_mN'], 3.92686, places=4)
        self.assertLess(max(touch['free_force_residual_nN'], released['free_force_residual_nN']), 2.)

    def test_subdivided_working_strand(self):
        fine = balance(EXAMPLES / 'downstream_fine.npz')
        self.assertGreater(fine['free_nodes'], 122)
        self.assertGreater(fine['downstream_eye_force_mN'], 0.)
        self.assertLess(fine['free_force_residual_nN'], 1000.)

    def test_registered_carrier_meter(self):
        self.assertAlmostEqual(meter(12.)['carrier_end_z_mm'],160.495,places=3)
        self.assertAlmostEqual(meter()['carrier_end_z_mm'],175.56176249,places=6)
        self.assertAlmostEqual(meter()['donated_rest_mm'],41.21050569,places=6)
        self.assertEqual(meter(0.)['stroke_mm'],0.)
        with self.assertRaises(ValueError):
            meter(100.)

    def test_fresh_limbs_bracket_the_eye_on_both_loop_disks(self):
        result = measure()
        self.assertAlmostEqual(result['eye_center_material_mm'], 1076.731605, places=5)
        for name, near, far in [('L0',1068.869104,1078.399195),('L1',1053.968589,1094.157239)]:
            loop = result['loops'][name]
            self.assertTrue(loop['two_limbs'])
            self.assertEqual(loop['signs'], [1,-1])
            self.assertAlmostEqual(loop['marks_mm'][0], near, places=5)
            self.assertAlmostEqual(loop['marks_mm'][1], far, places=5)
        self.assertAlmostEqual(meter(57.270550905)['carrier_end_z_mm'],183.846121,places=5)
