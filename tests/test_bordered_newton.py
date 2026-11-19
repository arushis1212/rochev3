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

 def test_near_equilibrium_energy_roundoff_still_requires_force_convergence(self):
  H=np.diag([1e-3,2.,3.,4.]);target=np.zeros(4)
  def f(x):return 1e8+.5*x@H@x,H@x
  x,r=minimize_bordered(f,np.array([2e-4,0,0,0]),2,lambda x:True,maxiter=10)
  self.assertTrue(r['optimizer_success']);self.assertLess(np.max(abs(H@x)),1e-8)

 def test_spectral_metric_handles_indefinite_curvature_without_changing_energy(self):
  def f(x):return (x[0]*x[0]-1)**2+.5*x[1]*x[1],np.array([4*x[0]*(x[0]*x[0]-1),x[1]])
  for metric in [True,'absolute']:
   x,r=minimize_bordered(f,np.array([.1,.2]),1,lambda x:True,maxiter=50,spectral=metric)
   self.assertTrue(r['optimizer_success']);self.assertAlmostEqual(x[0],1,places=7);self.assertLess(abs(x[1]),1e-8)

 def test_absolute_damping_corrects_stiff_contact_without_scaling_it_away(self):
  H=np.diag([1e-8,1e4]);linear=np.array([.01,0.])
  def f(x):return .5*x@H@x+linear@x,H@x+linear
  start=np.array([0.,.0014]);x,r=minimize_bordered(f,start,1,lambda x:True,maxiter=1,max_step=1.,spectral='absolute_damped')
  self.assertLess(abs(f(x)[1][1]),.001);self.assertLessEqual(abs(x-start).max(),1.);self.assertLess(f(x)[0],f(start)[0]);self.assertFalse(r['optimizer_success'])
