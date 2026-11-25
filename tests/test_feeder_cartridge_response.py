import json
import unittest

from cad.feeder_cartridge.response import DATA, displacement


class CartridgeResponseTests(unittest.TestCase):
    def test_full_static_and_harmonic_solutions(self):
        data=json.loads(DATA.read_bytes())
        for key,case in data['cases'].items():
            self.assertAlmostEqual(displacement(1.,0.,int(key)),case['static_response_mm_per_N'],places=10)
            for reference in case['full_FE_harmonic_checks']:
                expected=reference['response_mm_per_N']
                actual=displacement(1.,reference['frequency_Hz'],int(key))
                self.assertLess(abs(actual/expected-1),2e-7)

    def test_force_sign_and_range(self):
        self.assertEqual(displacement(-10.),-displacement(10.))
        with self.assertRaises(ValueError):
            displacement(10.,20000.)
