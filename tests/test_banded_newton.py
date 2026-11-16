import unittest
import numpy as np
from physics.banded_newton import banded_hessian,minimize_banded
from physics.roche_rod import energy_gradient,contact_energy
class NewtonChecks(unittest.TestCase):
    def test_hessian_matches_individual_column_differences(self):
        q=np.column_stack([np.linspace(-2,2,9),.1+.04*np.cos(np.linspace(0,3,9))]);ends=q[[0,-1]];rest=np.full(8,.5)
        def fun(x):
            p=np.vstack([ends[0],x.reshape(-1,2),ends[1]])
            E,g=energy_gradient(p,rest,2.,.02);C,h=contact_energy(p,.3,10.,{'half_width':3.,'bottom':-2.,'top':0.},samples=8,rest=rest)
            return E+C,(g+h)[1:-1].ravel()
        x=q[1:-1].ravel();h=1e-5;H=np.column_stack([(fun(x+np.eye(len(x))[j]*h)[1]-fun(x-np.eye(len(x))[j]*h)[1])/(2*h) for j in range(len(x))]);B=banded_hessian(fun,x,5)
        for d in range(6):np.testing.assert_allclose(B[d,:len(x)-d],np.diag((H+H.T)/2,-d),rtol=1e-7,atol=1e-7)
    def test_positive_quadratic_converges_to_known_solution(self):
        A=np.diag(np.arange(1.,11.))+np.diag(np.full(9,-.1),1)+np.diag(np.full(9,-.1),-1);target=np.linspace(-.1,.1,10)
        def fun(x):d=x-target;return .5*d@A@d,A@d
        x,r=minimize_banded(fun,np.ones(10),1)
        self.assertTrue(r['optimizer_success']);np.testing.assert_allclose(x,target,atol=1e-7)
        self.assertTrue(r['energy_monotone'])
