import unittest

import numpy as np

from examples.receiver_probe import crossings, measure, segment_distance


class ReceiverProbeTests(unittest.TestCase):
    def test_parallel_and_crossing_segments(self):
        a,b,c,d=np.array([[0.,0.,0.],[2.,0.,0.],[1.,1.,0.],[3.,1.,0.]])
        self.assertAlmostEqual(segment_distance(a,b,c,d),1.)
        self.assertAlmostEqual(segment_distance(a,b,c,c-[0.,2.,0.]),0.)

    def test_probe_ends_before_plane(self):
        tri=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
        self.assertEqual(crossings(np.array([.2,.2,2.]), np.array([.2,.2,1.]),tri),[])

    def test_both_registered_openings(self):
        r=measure()
        self.assertEqual([v[1] for v in r['old']],[-1])
        self.assertEqual([v[1] for v in r['drawn']],[-1])
        self.assertAlmostEqual(r['drawn'][0][0]-r['old'][0][0],22.7017628893,places=6)
        self.assertAlmostEqual(r['yarn_skin_gap_mm'],.9505507062,places=7)
        self.assertAlmostEqual(r['hardware_gap_mm'],1.5272607995,places=7)
        self.assertAlmostEqual(r['old_material'][0][0],901.7139920,places=6)
        self.assertAlmostEqual(r['drawn_material'][0][0],1038.9469628,places=6)
        self.assertEqual([x[1] for x in r['old_material']+r['drawn_material']],[-1,-1])
