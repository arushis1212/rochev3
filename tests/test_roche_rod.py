import unittest
import numpy as np
from physics.roche_rod import energy_gradient,contact_energy,box_distance,clearance_bound

class RodMechanics(unittest.TestCase):
    def test_uniform_extension_has_exact_energy_and_end_force(self):
        q=np.column_stack([np.linspace(0,10.1,11),np.zeros(11)])
        E,g=energy_gradient(q,np.ones(10),2.,.1)
        self.assertAlmostEqual(E,.5*2*10*.01**2,places=12)
        self.assertAlmostEqual(g[-1,0],.02,places=12)
        self.assertLess(np.max(np.abs(g[1:-1])),1e-12)

    def test_rod_gradient_and_rigid_motion_invariance(self):
        q=np.array([[0.,0.],[.8,.3],[1.9,.5],[2.8,.1]])
        rest=np.ones(3);E,g=energy_gradient(q,rest,2.,.02)
        h=1e-6;numeric=np.zeros_like(q)
        for i in range(len(q)):
            for j in range(2):
                a=q.copy();b=q.copy();a[i,j]+=h;b[i,j]-=h
                numeric[i,j]=(energy_gradient(a,rest,2.,.02)[0]-energy_gradient(b,rest,2.,.02)[0])/(2*h)
        np.testing.assert_allclose(g,numeric,rtol=1e-6,atol=1e-8)
        R=np.array([[np.cos(.7),-np.sin(.7)],[np.sin(.7),np.cos(.7)]])
        self.assertAlmostEqual(energy_gradient(q@R.T+[3,4],rest,2.,.02)[0],E,places=12)
        np.testing.assert_allclose(g.sum(axis=0),0,atol=1e-12)

    def test_small_deflection_cantilever_energy_converges(self):
        # Euler-Bernoulli y=F*x^2*(3L-x)/(6B); integral B*y''^2/2=F^2 L^3/(6B).
        F=1e-4;L=1.;B=1.;exact=F*F*L**3/(6*B);errors=[]
        for n in (17,33,65):
            x=np.linspace(0,L,n);q=np.column_stack([x,F*x*x*(3*L-x)/(6*B)])
            E,_=energy_gradient(q,np.full(n-1,L/(n-1)),0.,B);errors.append(abs(E-exact)/exact)
        self.assertGreater(errors[0],errors[1]);self.assertGreater(errors[1],errors[2]);self.assertLess(errors[-1],.025)

    def test_contact_gradient(self):
        q=np.array([[-1.,.1],[0.,.2],[1.,.1]]);box={'half_width':2.,'bottom':-1.,'top':0.}
        E,g=contact_energy(q,.3,10.,box);h=1e-6;numeric=np.zeros_like(q)
        for i in range(len(q)):
            for j in range(2):
                a=q.copy();b=q.copy();a[i,j]+=h;b[i,j]-=h
                numeric[i,j]=(contact_energy(a,.3,10.,box)[0]-contact_energy(b,.3,10.,box)[0])/(2*h)
        np.testing.assert_allclose(g,numeric,atol=1e-7)

    def test_uniform_contact_energy_invariant_to_edge_subdivision(self):
        box={'half_width':20.,'bottom':-1.,'top':0.}
        values=[]
        for n in (5,9,17):
            q=np.column_stack([np.linspace(-4,4,n),np.full(n,.2)])
            rest=np.full(n-1,8/(n-1))
            values.append(contact_energy(q,.3,10.,box,samples=8,rest=rest)[0])
        np.testing.assert_allclose(values,.5*10*8*.1**2,rtol=1e-12)

    def test_continuous_bound_detects_between_node_intersection(self):
        box={'half_width':.8128,'bottom':-2.,'top':-.6}
        q=np.array([[-4.,-1.],[4.,-1.]])
        self.assertLess(clearance_bound(q,.3,box)['continuous_polyline_gap_lower_bound_mm'],0)
        q[:,1]=0.
        self.assertGreater(clearance_bound(q,.3,box)['continuous_polyline_gap_lower_bound_mm'],.29)

    def test_temporal_bound_finds_clear_endpoints_crossing_obstacle(self):
        from physics.roche_rod import transition_clearance_bound
        box={'half_width':.8,'bottom':-2.,'top':-.6}
        a=np.array([[-.2,0.],[.2,0.]]);b=a+[0,-3.]
        self.assertGreater(clearance_bound(a,.3,box)['continuous_polyline_gap_lower_bound_mm'],0)
        self.assertGreater(clearance_bound(b,.3,box)['continuous_polyline_gap_lower_bound_mm'],0)
        self.assertLess(transition_clearance_bound(a,b,.3,box),0)

if __name__=='__main__':unittest.main()
