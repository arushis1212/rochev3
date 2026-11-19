import unittest,json
from pathlib import Path
import numpy as np
from physics.roche_contact3d import polygon_distance,extrusion_distance,HookContact,contact_energy3d,closest_segments,self_pairs,self_contact
from physics.roche_rod import energy_gradient

class Contact3D(unittest.TestCase):
    def test_polygon_and_extrusion_analytic_box(self):
        profile={'profile_axes':[0,1],'extrusion_axis':2,'extrusion_bounds_mm':[-1,1],'outer':{'points':[[-2,-3],[2,-3],[2,3],[-2,3]]},'holes':[]}
        p=np.array([[0.,0.,0.],[3,4,2],[0,0,2],[0,2.5,0]])
        d,g=extrusion_distance(p,profile)
        np.testing.assert_allclose(d,[-1,np.sqrt(3),1,-.5])
        np.testing.assert_allclose(g[1],[1,1,1]/np.sqrt(3))
    def test_hole_distance(self):
        profile={'profile_axes':[0,1],'extrusion_axis':2,'extrusion_bounds_mm':[-2,2],'outer':{'points':[[-3,-3],[3,-3],[3,3],[-3,3]]},'holes':[{'points':[[-1,-1],[1,-1],[1,1],[-1,1]]}]}
        d,_=extrusion_distance(np.array([[.3,0,0],[1.5,0,0]]),profile)
        np.testing.assert_allclose(d,[.7,-.5])
    def test_3d_energy_gradient_and_invariance(self):
        q=np.array([[0.,0.,0.],[.8,.3,.1],[1.9,.5,-.3],[2.8,.1,.2]]);rest=np.ones(3)
        E,g=energy_gradient(q,rest,2.,.02);self.check_gradient(lambda q:energy_gradient(q,rest,2.,.02),q)
        Q,_=np.linalg.qr(np.array([[.3,.4,.5],[.1,-.7,.2],[.7,.2,.1]]))
        self.assertAlmostEqual(energy_gradient(q@Q+[1,4,3],rest,2.,.02)[0],E,places=12)
    def check_gradient(self,fn,q):
        E,g=fn(q);h=1e-6;numeric=np.zeros_like(q)
        for i in range(len(q)):
            for j in range(3):
                a=q.copy();b=q.copy();a[i,j]+=h;b[i,j]-=h
                numeric[i,j]=(fn(a)[0]-fn(b)[0])/(2*h)
        np.testing.assert_allclose(g,numeric,atol=2e-6,rtol=2e-5)
    def test_actual_profile_contact_gradient(self):
        p=Path(__file__).resolve().parents[1]/'cad/r5m2/generated/contact_profiles.json';o=HookContact(json.loads(p.read_text())['profiles'])
        q=np.array([[-.1,-.4,-1.5],[.1,-.4,0],[.2,-.4,1.5]])
        self.check_gradient(lambda q:contact_energy3d(q,np.array([1.5,1.5]),.3,1000,o),q)
    def test_segment_distance_interior_boundary_parallel(self):
        a=np.array([[0.,0.,0.]]);b=np.array([[2.,0.,0.]])
        for c,d,expected in [([[1,-1,1]],[[1,1,1]],1),([[3,-1,0]],[[3,1,0]],1),([[0,2,0]],[[2,2,0]],2)]:
            dist,_,_,_=closest_segments(a,b,np.array(c,dtype=float),np.array(d,dtype=float));self.assertAlmostEqual(dist[0],expected)
    def test_self_contact_gradient_and_force_balance(self):
        q=np.array([[0.,0.,0.],[2.,0.,0.],[3.,2.,0.],[1.,2.,.3],[1.,-1.,.3]])
        rest=np.linalg.norm(np.diff(q,axis=0),axis=1);pairs=self_pairs(rest,.3)
        self.check_gradient(lambda p:self_contact(p,rest,.3,10,pairs)[:2],q)
        _,g,gap=self_contact(q,rest,.3,10,pairs);self.assertLess(gap,0);np.testing.assert_allclose(g.sum(axis=0),0,atol=1e-12)
    def test_contact_profiles_match_cad_boundary(self):
        import cadquery as cq
        from cad.r5m2 import build
        root=Path(__file__).resolve().parents[1]
        profiles=json.loads((root/'cad/r5m2/generated/contact_profiles.json').read_text())
        solids=build.parts();rng=np.random.default_rng(22)
        points=rng.uniform([-5,-3,-2],[6,5,2],size=(16,3))
        for name,profile in profiles['profiles'].items():
            shape=solids[name].val();d,_=extrusion_distance(points,profile)
            for p,approx in zip(points,d):
                vertex=cq.Vertex.makeVertex(*map(float,p))
                exact=min(face.distance(vertex) for face in shape.Faces())
                if shape.isInside(cq.Vector(*map(float,p)),1e-8):exact=-exact
                self.assertLessEqual(abs(approx-exact),1e-8,(name,p,approx,exact))
    def test_straight_refinement_has_no_false_self_contact(self):
        for n in (17,33,65,129):
            q=np.column_stack([np.linspace(0,16,n),np.zeros(n),np.zeros(n)])
            rest=np.linalg.norm(np.diff(q,axis=0),axis=1)
            E,g,gap=self_contact(q,rest,.3,1000,self_pairs(rest,.3))
            self.assertEqual(E,0.);self.assertGreater(gap,0);np.testing.assert_array_equal(g,0)
