import math
import unittest
from examples.two_contact_section import Compliance


class TwoContactSection(unittest.TestCase):
    def test_all_active_sets(self):
        model=Compliance(1.,.25,1.)
        for gaps,wanted in [((.2,.1),(False,False)),((-.2,.1),(True,False)),
                            ((.2,-.1),(False,True)),((-.3,-.2),(True,True))]:
            p,g,e=model.contact(*gaps)
            self.assertEqual(tuple(x>0 for x in p),wanted)
            for load,gap in zip(p,g):
                self.assertGreaterEqual(gap,-1e-14)
                self.assertAlmostEqual(load*gap,0.)
            self.assertGreaterEqual(e,0.)

    def test_diagonal(self):
        p,g,e=Compliance(.25,0.,.5).contact(-.1,-.05)
        self.assertAlmostEqual(p[0],.4)
        self.assertAlmostEqual(p[1],.1)
        self.assertAlmostEqual(e,.0225)

    def test_cross_compliance_unloads_neighbor(self):
        p,g,_=Compliance(1.,.5,1.).contact(-.2,-.03)
        self.assertAlmostEqual(p[0],.2)
        self.assertEqual(p[1],0.)
        self.assertAlmostEqual(g[1],.07)

    def test_virtual_work_inside_and_across_switch(self):
        model=Compliance(.4,.12,.30)
        for gaps in [(-.12,-.09),(-.10,-.03),(-.10,.05),(.14,-.1),(.1,.1)]:
            p,_,_=model.contact(*gaps)
            for axis in (0,1):
                h=1e-7
                plus=list(gaps);minus=list(gaps);plus[axis]+=h;minus[axis]-=h
                derivative=(model.contact(*plus)[2]-model.contact(*minus)[2])/(2*h)
                self.assertAlmostEqual(derivative,-p[axis],delta=3e-7)

    def test_swap_axes(self):
        for gaps in [(-.12,-.09),(-.05,.04),(.1,-.1)]:
            p,g,e=Compliance(.4,-.07,.3).contact(*gaps)
            q,h,f=Compliance(.3,-.07,.4).contact(*reversed(gaps))
            for l,r in zip((*p,*g,e),(*reversed(q),*reversed(h),f)):
                self.assertAlmostEqual(l,r)

    def test_invalid(self):
        for m in [Compliance(0.,0.,1.),Compliance(1.,2.,1.),Compliance(1.,1.,1.),Compliance(1.,math.nan,1.)]:
            with self.assertRaises(ValueError):
                m.contact(0.,-.01)
