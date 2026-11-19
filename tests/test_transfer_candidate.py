import unittest,json
from pathlib import Path
import numpy as np
from physics.roche_contact3d import extrusion_distance,contact_energy3d
from physics.transfer_contact import TransferContact,transfer_metrics
ROOT=Path(__file__).resolve().parents[1]
class TransferCandidate(unittest.TestCase):
    def test_profiles_against_independent_cad_distances(self):
        import cadquery as cq
        from cad.transfer.build import parts
        ps=parts();profiles=json.loads((ROOT/'cad/transfer/generated/contact_profiles.json').read_text());rng=np.random.default_rng(310)
        for name,profile in profiles.items():
            shape=ps['H02_contact_blade' if name=='H02_gate' else name].val()
            lo,hi=([-10,-3,-2],[6,5,2]) if name.startswith('H') else ([-3,-8,-11],[3,9,11])
            pts=rng.uniform(lo,hi,size=(24,3));d,_=extrusion_distance(pts,profile)
            for p,value in zip(pts,d):
                exact=min(f.distance(cq.Vertex.makeVertex(*map(float,p))) for f in shape.Faces())
                if shape.isInside(cq.Vector(*map(float,p)),1e-8):exact=-exact
                self.assertLess(abs(value-exact),1e-8,(name,p,value,exact))
    def test_stripper_force_is_gradient_of_energy(self):
        profiles=json.loads((ROOT/'cad/transfer/generated/contact_profiles.json').read_text());ob=TransferContact(profiles,3.,16.5)
        q=np.array([[.6,-1.,-4.],[.65,.2,-3.],[.6,.4,-2.]])
        rest=np.linalg.norm(np.diff(q,axis=0),axis=1);E,g=contact_energy3d(q,rest,.3,1000.,ob,32);self.assertGreater(E,0.)
        num=np.zeros_like(g);h=1e-6
        for i in range(3):
            for j in range(3):
                a=q.copy();b=q.copy();a[i,j]+=h;b[i,j]-=h;num[i,j]=(contact_energy3d(a,rest,.3,1000.,ob,32)[0]-contact_energy3d(b,rest,.3,1000.,ob,32)[0])/(2*h)
        np.testing.assert_allclose(num,g,rtol=1e-5,atol=1e-6)
    def test_transfer_metric_rejects_retained_pocket_and_nose_only(self):
        cfg=json.loads((ROOT/'spec/transfer_candidate.json').read_text());tool=json.loads((ROOT/'spec/r5_m2_fixture.json').read_text())['tool']
        p=np.array([[0.,.3,-2.],[0.,.3,2.]])
        self.assertFalse(transfer_metrics(p,0,0,cfg,tool,.3)['finite_radius_crossing_on_shaft'])
        p[:,0]=-8.5;p[:,1]=3.7
        self.assertTrue(transfer_metrics(p,0,0,cfg,tool,.3)['finite_radius_crossing_over_gate'])
        p[:,0]=5.1
        self.assertFalse(transfer_metrics(p,0,0,cfg,tool,.3)['finite_radius_crossing_clear_of_nose'])
    def test_simultaneous_contacts_sum_reactions_and_energies(self):
        class TwoPlanes:
            def components(self,p):
                normal=np.tile([1.,0.,0.],(len(p),1))
                return [(p[:,0]+.25,normal),(.25-p[:,0],-normal)]
        q=np.array([[0.,0.,0.],[0.,1.,0.]])
        E,g=contact_energy3d(q,np.array([1.]),.3,1000.,TwoPlanes(),8)
        self.assertAlmostEqual(E,2.5,places=12);np.testing.assert_allclose(g,0,atol=1e-12)
        q[:,0]=.01
        E,g=contact_energy3d(q,np.array([1.]),.3,1000.,TwoPlanes(),8)
        self.assertAlmostEqual(E,2.6,places=12);np.testing.assert_allclose(g.sum(axis=0),[20.,0.,0.],atol=1e-10)
