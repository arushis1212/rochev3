import unittest

import numpy as np
from examples.mobile_yarn_contact import replay, yarn_contact


class MobileYarnContactTests(unittest.TestCase):
    def test_opposite_reactions_at_interior_crossing(self):
        points=np.array([[-1.,0,0],[1.,0,0],[0,-1,.6],[0,1,.6]])
        row,gap=yarn_contact(points,np.arange(4),.3)
        self.assertAlmostEqual(gap,0.)
        np.testing.assert_allclose(row[:2,2],[-.5,-.5])
        np.testing.assert_allclose(row.sum(axis=0),0.)
        np.testing.assert_allclose(np.cross(points,row).sum(axis=0),0.)

    def test_saved_handoff(self):
        r=replay()
        self.assertEqual((r["working_nodes"],r["foundation_nodes"]),(122,114))
        self.assertEqual(r["accepted_steps"],132)
        self.assertAlmostEqual(r["end_ms"],2.5)
        self.assertLess(r["first_strand_contact_ms"],r["first_needle_contact_ms"])
        self.assertAlmostEqual(r["first_needle_contact_ms"],1.33405488,places=6)
        self.assertAlmostEqual(r["end_needle_load_mN"],6.305983,places=4)
        self.assertLess(r["maximum_free_residual_uN"],1.)
        self.assertLess(r["maximum_reciprocal_force_error_N"],1e-12)
        self.assertGreater(r["maximum_foundation_displacement_mm"],.1)
        self.assertGreater(r["yarn_normal_impulse_uNs"],0.)
