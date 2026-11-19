import math
import unittest

from examples.gravity_carrier import equilibrium, response


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
