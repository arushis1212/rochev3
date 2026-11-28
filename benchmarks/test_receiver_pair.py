import json
from math import dist, hypot
from pathlib import Path
import unittest


class ReceiverPair(unittest.TestCase):
    def test_two_finite_pin_tangencies(self):
        root = Path(__file__).resolve().parents[1]
        fit = json.loads((root/'cad/castoff/receiver_pair.json').read_text())
        axis = fit['axis_toward_carrier']
        a,b = fit['pins']
        self.assertAlmostEqual(hypot(*axis),1.,places=10)
        self.assertAlmostEqual(dist(a['axis_center_xyz_mm'], b['axis_center_xyz_mm']), fit['pitch_mm'],places=9)
        self.assertLess(a['touch_material_mm'], fit['mark_mm'])
        self.assertGreater(b['touch_material_mm'], fit['mark_mm'])
        for pin in fit['pins']:
            d = [v-u for v,u in zip(pin['yarn_center_xyz_mm'],pin['axis_center_xyz_mm'])]
            h = sum(x*y for x,y in zip(axis,d))
            self.assertGreater(h,-fit['tip_forward_mm'])
            self.assertLess(h,fit['carrier_front_mm'])
            radial_distance = hypot(*(v-h*u for v,u in zip(d,axis)))
            self.assertAlmostEqual(radial_distance,fit['pin_diameter_mm']/2+fit['yarn_radius_mm'],places=7)
            self.assertGreaterEqual(pin['steel_lower_bound_mm'],.4)

    def test_load_transfers_to_four_receiver_faces(self):
        root = Path(__file__).resolve().parents[1]
        case = json.loads((root/'cad/castoff/receiver_load.json').read_text())
        states = case['stations']
        self.assertEqual(len(states),37)
        self.assertEqual(case['nodes_in_local_balance'],15)
        self.assertTrue(all(s['gate_deg']==110. for s in states))
        self.assertTrue(all(s['maximum_local_residual_mN']<.001 for s in states))
        self.assertGreater(states[0]['original_eye_load_mN'],0.)
        self.assertEqual(states[-1]['original_eye_load_mN'],0.)
        self.assertEqual(states[-1]['eye_sections'],[0]*5)
        self.assertEqual(states[-1]['withdrawal_mm'],2.5)
        self.assertEqual(states[-1]['jaw_deg'],-75.)
        self.assertTrue(all(states[-1]['face_loads_mN'][f'seat_{n}']>38. for n in range(4)))
