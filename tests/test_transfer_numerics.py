import unittest
import numpy as np
from physics.roche_contact3d import contact_energy3d
from physics.loop_holding import contact_counts,valid_inverse_hessian
from physics.banded_newton import banded_hessian

class Plane:
    def distance(self,p):
        g=np.zeros_like(p);g[:,2]=np.where(p[:,2]>=0,1.,-1.)
        return abs(p[:,2]),g

class TransferNumerics(unittest.TestCase):
    def test_long_edge_contact_against_exact_integral(self):
        q=np.array([[0.,0.,-16.],[0.,0.,16.]]);rest=np.array([32.]);r=.3;k=1000.
        sparse,_=contact_energy3d(q,rest,r,k,Plane(),32)
        self.assertEqual(sparse,0.)  # The previous rule misses this whole contact.
        counts=contact_counts(rest,{'contact_samples_per_edge':32,'contact_reference_spacing_mm':.025})
        E,g=contact_energy3d(q,rest,r,k,Plane(),counts)
        self.assertLess(abs(E-k*r**3/3)/(k*r**3/3),.002)
        for i in [0,1]:
            a=q.copy();b=q.copy();a[i,2]+=1e-6;b[i,2]-=1e-6
            num=(contact_energy3d(a,rest,r,k,Plane(),counts)[0]-contact_energy3d(b,rest,r,k,Plane(),counts)[0])/2e-6
            self.assertAlmostEqual(num,g[i,2],places=7)
    def test_variable_edge_counts_keep_reference_weights(self):
        q=np.array([[0.,0.,.2],[1.,0.,.2],[4.,0.,.2]]);rest=np.array([1.,3.])
        E,g=contact_energy3d(q,rest,.3,1000.,Plane(),[7,61])
        self.assertAlmostEqual(E,20.,places=12)
        np.testing.assert_allclose(g.sum(axis=0),[0.,0.,-400.],atol=1e-10)
        with self.assertRaises(ValueError):contact_energy3d(q,rest,.3,1000.,Plane(),[0,1])
    def test_full_hessian_does_not_evaluate_empty_colors(self):
        A=np.array([[2.,.1,.2],[.1,3.,.4],[.2,.4,4.]]);calls=[]
        def f(x):calls.append(1);return .5*x@A@x,A@x
        H=banded_hessian(f,np.ones(3),2)
        self.assertEqual(len(calls),6)
        for d in range(3):np.testing.assert_allclose(H[d,:3-d],np.diag(A,-d),atol=1e-9)
    def test_invalid_search_metric_cannot_enter_optimizer(self):
        self.assertIsNone(valid_inverse_hessian([[1.,0],[0,-1.]],2))
        self.assertIsNone(valid_inverse_hessian([[np.nan]],1))
        self.assertIsNone(valid_inverse_hessian(np.eye(2),3))
        np.testing.assert_allclose(valid_inverse_hessian([[2.,.2],[.2,1.]],2),[[2.,.2],[.2,1.]])

    def test_broadphase_retains_all_exact_penalty_contacts(self):
        import json
        from pathlib import Path
        from physics.roche_contact3d import extrusion_distance,extrusion_contact_distance
        root=Path(__file__).resolve().parents[1]
        profiles=json.loads((root/'cad/transfer/generated/contact_profiles.json').read_text())
        rng=np.random.default_rng(73)
        for profile in profiles.values():
            p=rng.uniform([-65,-20,-15],[15,20,15],size=(3000,3))
            d,g=extrusion_distance(p,profile);x,h=extrusion_contact_distance(p,profile,.3)
            np.testing.assert_allclose(np.maximum(.3-d,0),np.maximum(.3-x,0),atol=1e-12)
            np.testing.assert_allclose(np.maximum(.3-d,0)[:,None]*g,np.maximum(.3-x,0)[:,None]*h,atol=1e-12)

    def test_interpolation_guard_rejects_plane_crossing(self):
        from physics.transfer_safe_continuation import transition_bounds
        q=np.array([[0.,0.,.31],[1.,0.,.31]])
        other=q.copy();other[:,2]*=-1
        b=transition_bounds(q,other,[0,0,0],[0,0,0],.01,.01,1.,1.,.3)
        self.assertLessEqual(b['solid_centerline_bound_mm'],0)
        other=q.copy();other[:,0]+=.1
        b=transition_bounds(q,other,[0,0,0],[0,0,0],.01,.01,1.,1.,.3)
        self.assertGreater(b['solid_centerline_bound_mm'],0)
