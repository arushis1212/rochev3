"""Geometry identity, independent dynamics, and frequency sensitivity of the brake."""
import hashlib
import json
import math
import unittest
from examples.fork_brake import SPEC,simulate

class TestForkBrake(unittest.TestCase):
    def test_travel_and_seating(self):
        s=json.loads(SPEC.read_text())
        self.assertEqual(hashlib.sha256((SPEC.parent/'receiver_drive.step').read_bytes()).hexdigest(),s['step_sha256'])
        self.assertGreater(s['minimum_seating_N'],0)
        self.assertGreater(s['pinned_buckling_N'],3*s['compression_bound_N'])
        omega=2*math.pi*s['nominal_axial_frequency_Hz']
        self.assertAlmostEqual(omega*((2*s['brake_distance_mm']/s['entry_speed_mm_s'])*(1-s['ramp_fraction'])),4*math.pi)
    def test_independent_integration(self):
        s=json.loads(SPEC.read_text());nominal=simulate(s)
        self.assertLess(abs(nominal['speed_mm_s']),1e-6)
        self.assertAlmostEqual(nominal['position_mm'],s['brake_distance_mm'],places=8)
        for factor in (.9,.95,1.,1.05,1.1):
            self.assertLess(simulate(s,factor)['peak_or_dwell_bound_mm'],s['stroke_available_mm'])

if __name__=='__main__':unittest.main()
