import math
import unittest

from examples.spool_payout import HelicalPayout


class HelicalPayoutTests(unittest.TestCase):
    def test_marked_payout_and_storage(self):
        first, last = 219.30876920587457, 359.8804517871325
        test = HelicalPayout.for_marks(first,last,7,.84)
        wound, takeoff, delivered = test.lengths(7)
        self.assertAlmostEqual(delivered,last-first,places=12)
        self.assertAlmostEqual(takeoff,5.88,places=12)
        self.assertAlmostEqual(wound,delivered+takeoff,places=12)

    def test_parametric_helix_reconstruction(self):
        spool = HelicalPayout(3.4,.84)
        n = 4096
        chord = math.hypot(2*spool.radius_mm*math.sin(math.pi/n),spool.pitch_mm/n)
        delta = spool.lengths(1)[0]-n*chord
        self.assertGreater(delta,0)
        self.assertLess(delta,3e-6)

    def test_flat_winding(self):
        spool = HelicalPayout.for_marks(0,100,2,0)
        self.assertAlmostEqual(2*math.pi*spool.radius_mm,50)
        self.assertAlmostEqual(spool.lengths(.5)[2],25)

    def test_straight_or_empty_winding(self):
        self.assertEqual(HelicalPayout(0,3).lengths(4),(12,12,0))
        self.assertEqual(HelicalPayout(0,0).lengths(4),(0,0,0))

    def test_high_pitch_retains_small_positive_delivery(self):
        radius, pitch = 1e-10,1
        net = HelicalPayout(radius,pitch).lengths(1)[2]
        self.assertAlmostEqual(net/((2*math.pi*radius)**2/(2*pitch)),1,places=14)

    def test_rejects_invalid_inputs(self):
        for args in ((-1,2,1,.8),(2,1,1,.8),(1,2,0,.8),(0,1,2,-1),(0,math.inf,2,.8)):
            with self.assertRaises(ValueError):
                HelicalPayout.for_marks(*args)
        with self.assertRaises(ValueError):
            HelicalPayout(1,2).lengths(-1)
