import unittest
import numpy as np
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from physics.bored_pin_contact import BoredPinCapsuleDistance


class BoredPinContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contact=BoredPinCapsuleDistance([0,0,0],1.5,4.2,.3,.9)
        pin=cq.Solid.makeCylinder(1.5,8.4,cq.Vector(0,-4.2,0),cq.Vector(0,1,0))
        channel=cq.Solid.makeCylinder(.3,4.,cq.Vector(0,0,.9),cq.Vector(0,0,1)).fuse(cq.Solid.makeSphere(.3,cq.Vector(0,0,.9),angleDegrees1=-90,angleDegrees2=90))
        cls.native=pin.cut(channel);cls.boundary=cq.Compound.makeCompound(cls.native.Faces())
        assert cls.native.isValid()

    def native_distance(self,point):
        query=BRepExtrema_DistShapeShape(cq.Vertex.makeVertex(*map(float,point)).wrapped,self.boundary.wrapped);query.Perform()
        self.assertTrue(query.IsDone());self.assertGreater(query.NbSolution(),0)
        distance=query.Value()
        if self.native.isInside(cq.Vector(*map(float,point)),1e-9):distance=-distance
        return distance

    def test_upper_rim_euclidean_distance(self):
        p=np.array([[0,0,1.8]])
        d,g=self.contact.distance(p)
        self.assertAlmostEqual(d[0],np.hypot(.3,.3),places=12)
        self.assertGreater(d[0],.3) # Nearest retained rim, including both radial and vertical offsets.
        self.assertAlmostEqual(d[0],self.native_distance(p[0]),places=9)
        self.assertAlmostEqual(np.linalg.norm(g[0]),1.,places=12)

    def test_native_distance_all_features_and_signs(self):
        explicit=np.array([[0,0,.6],[0,0,.9],[0,0,1.35],[0,.1,1.8],[.15,.1,1.6],
            [.2,.05,1.4],[.6,.2,1.2],[1.2,0,0],[2,5,2],[0,4.5,0],
            [0,0,0],[0,0,-1.2],[.29,.02,.7],[.2,.2,.9],[0,0,1.5],
            [.31,0,1.47],[-.31,0,1.47],[0,-.31,1.55]])
        random=np.random.default_rng(723).uniform([-2,-5,-2],[2,5,2.5],(180,3))
        rim=np.random.default_rng(841).uniform([-.5,-.5,1.2],[.5,.5,2.],(120,3))
        points=np.vstack((explicit,random,rim));d,_=self.contact.distance(points)
        native=np.array([self.native_distance(p)for p in points])
        np.testing.assert_allclose(d,native,atol=3e-7,rtol=0)

    def test_distance_gradient_and_one_lipschitz(self):
        p=np.array([[.08,.11,1.83],[.27,-.06,1.6],[.12,.18,1.2],
            [.1,.05,.4],[.8,.3,.7],[.2,4.4,.3],[1.7,4.5,-.7]])
        d,g=self.contact.distance(p);h=1e-6;fd=np.empty_like(p)
        for j in range(3):
            delta=np.zeros(3);delta[j]=h
            fd[:,j]=(self.contact.distance(p+delta)[0]-self.contact.distance(p-delta)[0])/(2*h)
        np.testing.assert_allclose(g,fd,atol=4e-7,rtol=0)
        np.testing.assert_allclose(np.linalg.norm(g,axis=1),1,atol=1e-12)
        perturb=np.random.default_rng(46).normal(0,.07,p.shape)
        d2,_=self.contact.distance(p+perturb)
        self.assertTrue(np.all(abs(d2-d)<=np.linalg.norm(perturb,axis=1)+1e-12))

    def test_translation_and_symmetry(self):
        p=np.array([[.1,.2,1.8],[.2,.1,.7],[-.8,.3,-1.]])
        d,g=self.contact.distance(p);shift=np.array([7.,-4.,12.])
        moved=BoredPinCapsuleDistance(shift,1.5,4.2,.3,.9)
        dm,gm=moved.distance(p+shift)
        np.testing.assert_allclose(dm,d,atol=2e-14);np.testing.assert_allclose(gm,g,atol=2e-13)
        for axis in (0,1):
            pp=p.copy();pp[:,axis]*=-1;ds,gs=self.contact.distance(pp);expected=g.copy();expected[:,axis]*=-1
            np.testing.assert_allclose(ds,d,atol=2e-14);np.testing.assert_allclose(gs,expected,atol=2e-13)

    def test_rim_global_minimum_not_one_local_projection(self):
        points=np.array([[0,0,1.8],[.2,.01,1.6],[.1,.3,1.7],[.1,.1,-2.],
            [0,0,1.49],[0,0,-1.],[0,.2,1.5],[.2,0,1.6]])
        closest=self.contact._rim_points(points)
        theta=np.linspace(0,2*np.pi,30001);rim=np.column_stack((.3*np.cos(theta),.3*np.sin(theta),np.sqrt(1.5**2-.3**2*np.cos(theta)**2)))
        for p,q in zip(points,closest):
            actual=np.linalg.norm(p-q);sampled=np.min(np.linalg.norm(rim-p,axis=1))
            self.assertLessEqual(actual,sampled+1e-12)
            self.assertLess(sampled-actual,1e-7)

    def test_nonfinite_and_unsupported_geometry_rejected(self):
        for args in [([0,0],1.5,4.2,.3,.9),([0,0,0],1.5,.2,.3,.9),([0,0,0],1.5,4.2,.3,1.3),([0,0,0],1.5,4.2,.3,.2),([0,0,0],float('nan'),4.2,.3,.9)]:
            with self.assertRaises(ValueError):BoredPinCapsuleDistance(*args)
        with self.assertRaises(ValueError):self.contact.distance([[0,0,np.inf]])
        with self.assertRaises(ValueError):self.contact.distance([0,0,0])
        d,g=self.contact.distance(np.empty((0,3)));self.assertEqual(d.shape,(0,));self.assertEqual(g.shape,(0,3))


if __name__=='__main__':unittest.main()
