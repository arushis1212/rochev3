import unittest,numpy as np
from physics.auxiliary_contact import AuxiliaryContact
from physics.roche_contact3d import contact_energy3d

class AuxiliaryCulling(unittest.TestCase):
 def test_energy_and_gradient_equal_unculled_boxes(self):
  boxes={'fixed':{'bbox_mm':[-1,1,-2,2,-3,3],'moves_with_lift':False},'moving':{'bbox_mm':[2,3,0,2,-1,1],'moves_with_lift':True}}
  rng=np.random.default_rng(921)
  for lift in [0.,3.]:
   ob=AuxiliaryContact(boxes,lift)
   class Dense:
    def components(self,p):return ob.components(p)
   for scale in [.2,3.,20.]:
    q=rng.normal(0,scale,(20,3));rest=np.linalg.norm(np.diff(q,axis=0),axis=1)
    a=contact_energy3d(q,rest,.3,10.,ob,8);b=contact_energy3d(q,rest,.3,10.,Dense(),8)
    for x,y in zip(a,b):np.testing.assert_allclose(x,y,atol=1e-10,rtol=1e-12)
