import math
import unittest
from examples.washer_support import bearing_area, supported_disk


class WasherSupport(unittest.TestCase):
    def test_complete_and_empty(self):
        self.assertAlmostEqual(bearing_area(3.,1.,.8,7.,.2),8*math.pi)
        self.assertEqual(bearing_area(3.,1.,1.,-4.,0.),0.)
        self.assertEqual(bearing_area(3.,1.,2.,0.,1.1),0.)

    def test_diameter_on_edge(self):
        self.assertAlmostEqual(bearing_area(3.,1.5,1.2,0.,0.),3.375*math.pi)

    def test_complement(self):
        for d in (-3.,-2.9,-1.,0.,.5,2.,3.):
            self.assertAlmostEqual(supported_disk(3.,d)+supported_disk(3.,-d),9*math.pi)

    def test_independent_chord_quadrature(self):
        # Integrate the actual displaced washer and plate bore by vertical slices.
        # For this horizontal offset the two removed bore chords share a centerline.
        outer,inner,bore,nominal,tol=3.,1.55,1.5,1.8,.18
        floor=bearing_area(outer,inner,bore,nominal,tol)
        chord=lambda r,x: 2*math.sqrt(max(0.,r*r-x*x))
        count=24000
        for offset in (-tol,-.12,0.,.08,tol):
            center=nominal+offset
            lo=max(0.,center-outer)
            dx=(center+outer-lo)/count
            total=0.
            for i in range(count):
                x=lo+(i+.5)*dx
                total+=max(0.,chord(outer,x-center)-max(chord(inner,x-center),chord(bore,x-nominal)))
            self.assertGreaterEqual(total*dx+1e-5,floor)
        disk=bearing_area(outer,inner,bore,nominal,0.)
        self.assertAlmostEqual(disk,bearing_area(outer,inner,0.,nominal,0.))
        self.assertAlmostEqual(disk, self.exact_alignment_quadrature(), places=4)

    @staticmethod
    def exact_alignment_quadrature():
        dx=4.8/40000
        value=0.
        for i in range(40000):
            x=(i+.5)*dx-1.8
            value+=2*(math.sqrt(max(0.,9-x*x))-math.sqrt(max(0.,1.55**2-x*x)))
        return dx*value

    def test_increasing_uncertainty(self):
        areas=[bearing_area(3.,1.55,1.5,1.8,e) for e in (0.,.05,.10,.18,.4)]
        self.assertEqual(areas,sorted(areas,reverse=True))

    def test_invalid_geometry(self):
        for args in ((1.,1.,1.,1.,0.),(3.,1.,-1.,1.,0.),(3.,1.,1.,1.,-.1),
                     (3.,1.,1.,math.inf,.1)):
            with self.assertRaises(ValueError):
                bearing_area(*args)
