import unittest
import numpy as np


class RigidPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from skfem import MeshTet,Basis,ElementVector,ElementTetP2,asm
        from skfem.models.elasticity import linear_elasticity,lame_parameters
        from physics.rigid_port_elastic import factor_port
        cls.L=30.;cls.E=2000.
        mesh=MeshTet.init_tensor(np.linspace(0,30,21),np.linspace(-1,1,3),np.linspace(-1,1,3))
        cls.basis=Basis(mesh,ElementVector(ElementTetP2()),intorder=4)
        cls.K=asm(linear_elasticity(*lame_parameters(cls.E,.3)),cls.basis)
        cls.fixed=cls.basis.get_dofs(lambda x:np.isclose(x[0],0)).all()
        cls.port=cls.basis.get_dofs(lambda x:np.isclose(x[0],30)).all()
        solve,meta=factor_port(cls.basis,cls.K,cls.fixed,cls.port,[30,0,0])
        cls.solve=staticmethod(solve);cls.meta=meta

    def test_cantilever_axial_and_transverse_closed_forms(self):
        for axis in range(3):
            w=np.zeros(6);w[axis]=1.;r=self.solve(port_wrench=w)
            expected=self.L/(self.E*4)if axis==0 else self.L**3/(3*self.E*(4/3))
            self.assertLess(abs(r['port_displacement'][axis]/expected-1),.03)
            self.assertLess(np.linalg.norm(r['report']['force_balance_N']),1e-8)
            self.assertLess(np.linalg.norm(r['report']['moment_balance_Nmm']),1e-7)
            self.assertAlmostEqual(r['report']['external_work_Nmm'],2*r['report']['strain_energy_Nmm'],places=8)

    def test_whole_port_compliance_reciprocal_and_positive(self):
        C=np.column_stack([self.solve(port_wrench=np.eye(6)[i])['port_displacement']for i in range(6)])
        np.testing.assert_allclose(C,C.T,atol=2e-9,rtol=1e-8)
        self.assertGreater(np.linalg.eigvalsh(C).min(),0.)

    def test_body_load_not_replaced_by_endpoint_force(self):
        from physics.linear_elastic_screen import uniform_body_force
        body=uniform_body_force(self.basis,[.01,0,0])
        r=self.solve(body_load=body)
        expected=.01*self.L**2/(2*self.E)
        self.assertLess(abs(r['port_displacement'][0]/expected-1),.03)

    def test_rigid_rotation_at_every_selected_node(self):
        from physics.rigid_port_elastic import port_map
        Q,meta=port_map(self.basis,self.fixed,self.port,[30,0,0])
        generalized=np.zeros(Q.shape[1]);generalized[-6:]=[.2,.3,.4,.01,-.02,.03]
        u=Q@generalized
        for axis,c in enumerate(meta['components']):
            ids=np.flatnonzero(np.isin(c,self.port));points=meta['coordinates_mm'][ids]
            expected=generalized[-6:-3]+np.cross(np.broadcast_to(generalized[-3:],points.shape),points-[30,0,0])
            np.testing.assert_allclose(u[c[ids]],expected[:,axis],atol=1e-14)
        np.testing.assert_array_equal(u[self.fixed],0.)

    def test_overlapping_or_incomplete_ports_rejected(self):
        from physics.rigid_port_elastic import port_map
        with self.assertRaises(ValueError):port_map(self.basis,self.fixed,self.fixed,[0,0,0])
        with self.assertRaises(ValueError):port_map(self.basis,self.fixed,self.port[:-1],[30,0,0])

    def test_fractional_boolean_multidimensional_and_out_of_bounds_dofs_rejected(self):
        from physics.rigid_port_elastic import port_map
        invalid=[self.fixed+.9,np.array([False,True]),self.fixed[:,None],
                 np.array([-1,0]),np.array([self.basis.N]),np.array([2**64-1],dtype=np.uint64)]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):port_map(self.basis,value,self.port,[30,0,0])
                with self.assertRaises(ValueError):port_map(self.basis,self.fixed,value,[30,0,0])


if __name__=='__main__':unittest.main()
