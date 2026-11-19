import unittest,numpy as np
from physics.material_mesh import refine_material
from physics.roche_rod import energy_gradient

class MaterialRefinement(unittest.TestCase):
 def test_preserves_uniform_strain_energy_and_material_attachments(self):
  q=np.array([[0.,0,0],[2.02,0,0],[5.05,0,0],[9.09,0,0]]);rest=np.array([2.,3.,4.]);energy,g=energy_gradient(q,rest,2.,.02)
  for factor in [1,2,4]:
   p,r,s=refine_material(q,rest,2,factor);e,gg=energy_gradient(p,r,2.,.02)
   self.assertAlmostEqual(sum(r),9.,places=12);self.assertAlmostEqual(e,energy,places=12);np.testing.assert_allclose(p[::factor],q,atol=1e-12);np.testing.assert_allclose(p[s],q[2]);np.testing.assert_allclose(gg[[0,-1]],g[[0,-1]],atol=1e-12)
 def test_invalid_refinement_rejected(self):
  for factor in [0,-1,1.5,True]:
   with self.assertRaises(ValueError):refine_material(np.zeros((3,3)),np.ones(2),1,factor)
