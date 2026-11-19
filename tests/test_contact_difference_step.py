"""Near-onset contact curvature must be resolved by the search metric."""
import unittest
import numpy as np
from physics.banded_newton import banded_hessian
from physics.bordered_newton import minimize_bordered
class ContactDifferenceStepTests(unittest.TestCase):
 def test_shallow_penalty_active_branch_curvature(self):
  # A rigid obstacle couples two coordinates. The exact active-branch Hessian
  # is known; an overly large central stencil straddles the contact onset.
  k=1000.;normal=np.array([.2,.8]);depth=2e-8
  def fun(x):
   d=max(0.,depth-normal@x)
   return .5*x@x+.5*k*d*d,x-k*d*normal
  x=np.zeros(2);expected=np.eye(2)+k*np.outer(normal,normal)
  def dense(h):
   A=banded_hessian(fun,x,1,h);return np.array([[A[0,0],A[1,0]],[A[1,0],A[0,1]]])
  self.assertLess(np.max(abs(dense(1e-9)-expected)),1e-8)
  self.assertGreater(np.max(abs(dense(1e-6)-expected)),100)
  y,info=minimize_bordered(fun,x,1,lambda q:False,step=1e-9,maxiter=20)
  self.assertTrue(info['optimizer_success']);self.assertLess(max(abs(fun(y)[1])),1e-8)
