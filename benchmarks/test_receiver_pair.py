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
