import math
import unittest
from fractions import Fraction
from examples.indexed_guide import envelope, indexed_path


class IndexedGuide(unittest.TestCase):
    def test_three_four_line(self):
        report = envelope(3,4,1.)
        self.assertEqual(report["last_notch"], (3,4))
        self.assertEqual(report["notches"],7)
        self.assertAlmostEqual(report["maximum_cross_track_mm"],.6)
        self.assertLessEqual(report["maximum_synchronized_error_mm"],1/math.sqrt(2))

    def test_tied_wheels_execute_separately(self):
        steps = list(indexed_path(1,1))
        self.assertIn((Fraction(1,2),1,0),steps)
        self.assertAlmostEqual(envelope(1,1,2)["maximum_cross_track_mm"],math.sqrt(2))

    def test_reflections_and_reversed_axis(self):
        for x,y in ((-3,4),(3,-4),(-3,-4),(4,3)):
            self.assertAlmostEqual(envelope(x,y,0.1)["maximum_cross_track_mm"],.06)

    def test_partial_stroke_zero_and_short_moves(self):
        self.assertEqual(envelope(0,0,1)["maximum_synchronized_error_mm"],0.)
        self.assertAlmostEqual(envelope("1/3",0,1)["maximum_synchronized_error_mm"],1/3)
        self.assertEqual(envelope(0,"-1/2",1)["last_notch"],(0,-1))
        self.assertEqual(envelope(0,-20,.1)["maximum_cross_track_mm"],0.)

    def test_between_vertices(self):
        dx,dy = Fraction(7,3), Fraction(11,4)
        vertices=list(indexed_path(dx,dy))
        report=envelope(dx,dy,1.)
        for a,b in zip(vertices,vertices[1:]):
            for k in range(17):
                t,x,y = (float((p*(16-k)+q*k)/16) for p,q in zip(a,b))
                self.assertLessEqual(abs(float(dx)*y-float(dy)*x)/math.hypot(dx,dy),report["maximum_cross_track_mm"]+1e-12)
                self.assertLessEqual(math.hypot(x-float(dx)*t,y-float(dy)*t),report["maximum_synchronized_error_mm"]+1e-12)

    def test_invalid_inputs(self):
        for bad in (0,-1,math.nan,math.inf):
            with self.assertRaises(ValueError):
                envelope(1,1,bad)
        with self.assertRaises(ValueError):
            envelope(.1,0,1)


if __name__ == "__main__":
    unittest.main()
