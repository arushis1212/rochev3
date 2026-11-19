import math
import unittest

from examples.gravity_carrier import equilibrium, load_envelope, response


class GravityCarrierTests(unittest.TestCase):
    def test_exact_manufactured_balance(self):
        # With x=6, z=8, the radius is 10 and the vertical direction cosine is 0.8.
        # Two 0.5 mm compressions at 1 N/mm therefore support exactly 0.8 N.
        result = equilibrium(6., 10.5, 1., .8/9.80665)
        self.assertAlmostEqual(result["height_mm"], 8., places=12)
        self.assertAlmostEqual(result["residual_n"], 0., places=13)
        self.assertAlmostEqual(result["vertical_stiffness_n_per_mm"], 2*(1-10.5*36/1000))

    def test_tangent_from_potential_gradient(self):
        for h in (7.6,8.1,8.5):
            force=lambda value:response(value,6.,10.5,4.,.25)[0]
            self.assertAlmostEqual((force(h+1e-6)-force(h-1e-6))/2e-6,
                                   response(h,6.,10.5,4.,.25)[1],places=7)

    def test_unloaded_contact(self):
        self.assertEqual(response(20.,6.,10.5,4.,.25),(.25,0.))

    def test_excessive_mass_and_nonfinite_dimensions(self):
        for mass in [4.0, math.nan]:
            with self.assertRaises(ValueError):
                equilibrium(6., mass_kg=mass)
        with self.assertRaises(ValueError):
            equilibrium(12.,contact_radius_mm=10.)

    def test_load_envelope_contains_interior_roots(self):
        # Center the manufactured 6–8–10 example at 0.8 N, then test ±0.1 N.
        band = load_envelope(6., 10.5, 1., .8/9.80665, .1)
        lo, hi = band["stable_height_interval_mm"]
        for i in range(21):
            load = .7 + .01*i
            root = equilibrium(6., 10.5, 1., load/9.80665)
            self.assertLessEqual(lo - 1e-13, root["height_mm"])
            self.assertLessEqual(root["height_mm"], hi + 1e-13)
            self.assertGreaterEqual(root["vertical_stiffness_n_per_mm"] + 1e-13,
                                    band["minimum_stiffness_n_per_mm"])
        self.assertAlmostEqual(response(lo, 6., 10.5, 1., .9)[0], 0.)
        self.assertAlmostEqual(response(hi, 6., 10.5, 1., .7)[0], 0.)

    def test_load_envelope_collapse_and_overload(self):
        fixed = load_envelope(6., 10.5, 1., .8/9.80665, 0.)
        self.assertEqual(*fixed["stable_height_interval_mm"])
        for bias in (-.1, math.inf, .8, 1.):
            with self.assertRaises(ValueError):
                load_envelope(6., 10.5, 1., .8/9.80665, bias)
        with self.assertRaises(ValueError):
            load_envelope(6., 10.5, 1., 4/9.80665, 1.)
