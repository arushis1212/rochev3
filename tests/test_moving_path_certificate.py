import unittest,numpy as np
from physics.auxiliary_contact import AuxiliaryContact
from physics.moving_path_certificate import certify_moving_path

class MovingPathCertificate(unittest.TestCase):
 def fixture(self,state):
  u=state[0];return AuxiliaryContact({'box':{'bbox_mm':[u-1,u+1,-1,1,-1,1],'moves_with_lift':False}})
 def test_large_safe_tangential_move_can_be_certified(self):
  a=np.array([[-.1,1.4,0.],[.1,1.4,0.]])+[0,0,0];b=a+[3.,0,0]
  r=certify_moving_path(a,b,[0,0,0],[.1,0,0],np.array([.2]),.3,self.fixture)
  self.assertTrue(r['certified']);self.assertGreater(r['subdivisions'],1)
 def test_translating_obstacle_crossing_is_rejected(self):
  a=np.array([[0.,-.1,0],[0.,.1,0]])
  r=certify_moving_path(a,a,[-2,0,0],[2,0,0],np.array([.2]),.3,self.fixture)
  self.assertFalse(r['certified'])
