import unittest
import numpy as np
from physics.continuation_predictor import predict
class PredictorTests(unittest.TestCase):
 def test_only_guess_changes_and_reversal_or_phase_switch_disables(self):
  q=np.array([[1.,0,0],[2,0,0]]);c=np.zeros(3);a=np.zeros(2);previous={'q':(q-.1).tolist(),'center':c.tolist(),'angles':a.tolist(),'state':[2,0,0,0]}
  got=predict(q,c,a,[1,0,0,0],[0,0,0,0],previous)[0];np.testing.assert_allclose(got,q+.1);np.testing.assert_array_equal(q,[[1,0,0],[2,0,0]])
  for target in [[2,0,0,0],[1,0,0,1]]:np.testing.assert_array_equal(predict(q,c,a,[1,0,0,0],target,previous)[0],q)
 def test_guess_displacement_bounded(self):
  q=np.zeros((2,3));prev={'q':[[-100,0,0],[-100,0,0]],'center':[0,0,0],'angles':[0,0],'state':[2,0,0,0]}
  p,*_=predict(q,np.zeros(3),np.zeros(2),[1,0,0,0],[0,0,0,0],prev);self.assertLessEqual(np.linalg.norm(p-q,axis=1).max(),1)
