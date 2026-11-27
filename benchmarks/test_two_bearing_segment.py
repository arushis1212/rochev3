import math
import unittest

from examples.two_bearing_segment import bearing_loads, closest_pin_contact


class TwoBearingTests(unittest.TestCase):
    def test_tangent_to_both_pins(self):
        for x in (2.,6.):
            hit = closest_pin_contact((0.,0.),(8.,0.),(x,-.9),.3,.6)
            self.assertEqual(hit.fraction, x/8)
            self.assertAlmostEqual(hit.clearance_mm, 0.)
            self.assertEqual(hit.normal, (0.,1.))

    def test_force_and_moment_balance(self):
        left, right = bearing_loads(.25,.75,2.5,3.5)
        self.assertEqual((left,right),(2.,4.))
        self.assertEqual(left+right,6.)
        self.assertEqual(2*left+6*right,8*3.5)

    def test_pin_contact_moves_to_endpoint(self):
        hit = closest_pin_contact((0.,0.),(1.,0.),(2.,0.),.1,.2)
        self.assertEqual(hit.fraction,1.)
        self.assertAlmostEqual(hit.clearance_mm,.7)

    def test_contact_can_just_unload(self):
        self.assertEqual(bearing_loads(.25,.75,3.,1.),(4.,0.))
        with self.assertRaises(ValueError):
            bearing_loads(.25,.75,4.,0.)

    def test_invalid_inputs(self):
        for t in (math.nan, .25, 2.):
            with self.assertRaises(ValueError):
                bearing_loads(.25,t,1.,1.)
        with self.assertRaises(ValueError):
            closest_pin_contact((0,0),(0,0),(1,2),.3,.5)
