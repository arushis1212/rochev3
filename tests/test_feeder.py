import json,math,unittest
from pathlib import Path
from physics.r5_feed_geometry import rope_length,counter_center,geometry_screen
class FeederGeometry(unittest.TestCase):
    def test_thin_cord_exact_limit(self):
        expected=32+76+80+8*math.pi
        for z in (130,160,190):
            self.assertAlmostEqual(rope_length(z+14,320-z+10,8),expected,places=9)
            self.assertAlmostEqual(counter_center(z+14,expected,8),320-z,places=8)
    def test_finite_cord_matches_spec(self):
        s=json.loads((Path(__file__).resolve().parents[1]/'spec/r5_m2_fixture.json').read_text())
        r=geometry_screen(s)
        self.assertAlmostEqual(r['effective_length_at_midstroke_mm'],s['feeder']['rope_geometric_length_mm'],places=8)
        for row in r['low_mode_positions']:self.assertLess(abs(row['CAD_error_mm']),1e-8)
