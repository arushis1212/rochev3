import unittest,numpy as np
from physics.bordered_newton import bordered_hessian,bordered_direction,minimize_bordered
class BorderedNewton(unittest.TestCase):
 def fixture(self):
  rng=np.random.default_rng(514);m=25;n=5
  A=np.diag(np.linspace(2,5,m))+np.diag(np.full(m-1,-.2),1)+np.diag(np.full(m-1,-.2),-1)
  B=rng.normal(0,.04,(m,n));C=np.eye(n)*2;H=np.block([[A,B],[B.T,C]]);target=rng.normal(0,.05,m+n)
  def f(x):d=x-target;return .5*d@H@d,H@d
  return f,H,target,m
 def test_hessian_and_schur_direction_against_dense_oracle(self):
  f,H,target,m=self.fixture();x=np.ones(len(target));A,B,C=bordered_hessian(f,x,m,8)
  for d in range(9):np.testing.assert_allclose(A[d,:m-d],np.diag(H[:m,:m],-d),atol=1e-9)
  np.testing.assert_allclose(B,H[:m,m:],atol=1e-9);np.testing.assert_allclose(C,H[m:,m:],atol=1e-9)
  for damping in [0.,.3]:np.testing.assert_allclose(bordered_direction(A,B,C,f(x)[1],damping),np.linalg.solve(H+damping*np.eye(len(x)),-f(x)[1]),atol=1e-8)
 def test_local_and_full_fallback_recover_known_equilibrium(self):
  f,H,target,m=self.fixture()
  for safe in [True,False]:
   x,r=minimize_bordered(f,np.ones(len(target)),m,lambda x:safe,maxiter=30)
   self.assertTrue(r['optimizer_success']);np.testing.assert_allclose(x,target,atol=1e-8)
   self.assertEqual(r['full_hessian_fallbacks']>0,not safe)
