import math
import unittest
from physics.crossed_rod_contact import continuum, pair_minimum


class CrossedRodContactTests(unittest.TestCase):
    def test_energy_derivative_is_exact_force(self):
        for diameter, separation, penalty in ((.6,.59998,1000.), (1.,.7,20.), (2.,1.,3.)):
            h = min(1e-7, (diameter-separation)/10000)
            energy, force = continuum(diameter, separation, penalty)
            derivative = (continuum(diameter,separation-h,penalty)[0]
                          - continuum(diameter,separation+h,penalty)[0])/(2*h)
            self.assertGreater(energy, 0)
            self.assertLess(abs(derivative/force-1), 1e-6)

    def test_refinement_approaches_analytic_integral(self):
        exact_energy, exact_force = continuum(.6,.59998,1000.)
        results = [pair_minimum(h,.6,.59998,1000.) for h in (.001,.0005,.0001,.00005)]
        for older, newer in zip(results, results[1:]):
            self.assertGreater(older[0], newer[0])
            self.assertGreater(older[1], newer[1])
        energy, force, _ = results[-1]
        self.assertGreaterEqual(energy, exact_energy)
        self.assertGreaterEqual(force, exact_force)
        self.assertLess(energy/exact_energy, 1.05)
        self.assertLess(force/exact_force, 1.04)

    def test_no_contact(self):
        for separation in (.6,.7):
            self.assertEqual(continuum(.6,separation,1000.), (0.,0.))
            self.assertEqual(pair_minimum(.01,.6,separation,1000.), (0.,0.,0))

    def test_input_and_compute_bounds(self):
        for bad in (0., -1., math.nan, math.inf):
            with self.assertRaises(ValueError): continuum(.6,bad,1000.)
            with self.assertRaises(ValueError): pair_minimum(bad,.6,.59998,1000.)
        with self.assertRaises(ValueError): pair_minimum(1e-10,.6,.59998,1000.)
        with self.assertRaises(ValueError): pair_minimum(.001,.6,.59998,1000.,True)


if __name__ == '__main__':
    unittest.main()
