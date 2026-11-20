import math
import unittest

from examples.indexed_load_transfer import common_housing_window, loaded_position, selectable_indices


class IndexedTransferTests(unittest.TestCase):
    def test_complementarity_through_both_transitions(self):
        for load in (5., 8., 11.):
            for i in range(-100,101):
                h = i/10000
                s = loaded_position(h, 0., load, .0005, .0001)
                self.assertAlmostEqual(s.rear_force+s.stop_force, load)
                self.assertGreaterEqual(min(s.rear_force,s.stop_force,s.rear_gap,s.stop_gap), 0.)
                self.assertAlmostEqual(s.rear_force*s.rear_gap, 0.)
                self.assertAlmostEqual(s.stop_force*s.stop_gap, 0.)
                self.assertAlmostEqual(s.rear_gap, h-s.carriage+.0005*s.rear_force)
                self.assertAlmostEqual(s.stop_gap, -s.carriage+.0001*s.stop_force)

    def test_gaps_at_measured_indices_hold_at_both_load_extremes(self):
        positions = [i*.0125 for i in range(-10,31)]
        for seat,compliance,limits in (("rear",.0005,(.005,.025)),("stop",.0001,(.20,.28))):
            window=common_housing_window(0.,limits,(5*compliance,11*compliance),loaded=seat)
            indices=selectable_indices(positions,window)
            self.assertTrue(indices)
            for index in indices:
                for force in (5.,8.,11.):
                    s=loaded_position(positions[index],0.,force,.0005,.0001)
                    gap=s.stop_gap if seat=="rear" else s.rear_gap
                    self.assertLessEqual(limits[0]-1e-12,gap)
                    self.assertLessEqual(gap,limits[1]+1e-12)

    def test_common_window_can_vanish_or_miss_a_notch(self):
        self.assertIsNone(common_housing_window(10.,(.005,.025),(0,.03),loaded="rear"))
        self.assertEqual(selectable_indices([1.,1.5],(1.1,1.4)),[])
        self.assertEqual(selectable_indices([1.,1.5],(1.,1.5)),[0,1])

    def test_continuity_and_directed_load_share(self):
        prior=0.
        for h in (-1.,-.0040000001,-.004,-.0039999999,0.,.0007999999,.0008,.0008000001,1.):
            s=loaded_position(h,0.,8.,.0005,.0001)
            self.assertGreaterEqual(s.stop_force,prior)
            prior=s.stop_force
        self.assertEqual(prior,8.)

    def test_invalid_or_nonfinite_inputs(self):
        for f in (0., -1., math.inf, math.nan):
            with self.assertRaises(ValueError): loaded_position(0.,0.,f,1.,1.)
        with self.assertRaises(ValueError): common_housing_window(0.,(0.,1.),(0.,1.),loaded="rear")
        with self.assertRaises(ValueError): common_housing_window(0.,(.1,1.),(0.,1.),loaded="spring")
        with self.assertRaises(ValueError): selectable_indices([1.,1.],(.1,.2))
