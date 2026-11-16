import unittest,numpy as np
from physics.loop_holding import rod_gravity
from cad.transfer.build import parts
from cad.transfer.interfaces import motion_shift
from physics.auxiliary_contact import AuxiliaryContact

class ResetPhysics(unittest.TestCase):
 def test_yarn_gravity_force_and_energy(self):
  q=np.array([[0.,0.,4.],[1.,2.,5.],[3.,4.,7.]]);rest=np.array([10.,20.]);rho=.1786
  E,g=rod_gravity(q,rest,rho);weight=30*rho*.00980665/1000
  self.assertAlmostEqual(g[:,2].sum(),weight);np.testing.assert_allclose(g[:,:2],0)
  self.assertAlmostEqual(rod_gravity(q+[0,0,2],rest,rho)[0]-E,2*weight)
  for i in range(3):
   a=q.copy();b=q.copy();a[i,2]+=1e-5;b[i,2]-=1e-5
   self.assertAlmostEqual((rod_gravity(a,rest,rho)[0]-rod_gravity(b,rest,rho)[0])/2e-5,g[i,2],places=10)
  with self.assertRaises(ValueError):rod_gravity(q,rest,-1)
 def test_reset_motion_is_not_applied_to_fixed_stops(self):
  self.assertEqual(motion_shift('R03_lift_pin_0',0,0,6,6),(6,6,0))
  self.assertEqual(motion_shift('R20_reset_sleeve',0,0,6,6),(0,6,0))
  spec={'p':{'bbox_mm':[0,1,0,1,0,1],'motion':'lift','resettable':True}}
  lo,hi=AuxiliaryContact(spec,6,0,0,6).bounds(spec['p']);np.testing.assert_allclose(lo,[6,6,0]);np.testing.assert_allclose(hi,[7,7,1])
 def test_real_axial_stops_admit_six_mm_and_reject_overtravel(self):
  p=parts();shuttle=p['R19_pin_shuttle'].val();stops=[p[n].val() for n in ['R21_reset_front_washer','R22_reset_rear_washer']]
  for q in [0,3,6]:self.assertLess(sum(shuttle.translate((q,0,0)).intersect(x).Volume() for x in stops),1e-7)
  for q in [-.01,6.01]:self.assertGreater(sum(shuttle.translate((q,0,0)).intersect(x).Volume() for x in stops),1e-7)
