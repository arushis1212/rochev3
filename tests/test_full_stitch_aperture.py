import unittest
import numpy as np
from physics.full_stitch_aperture import MaterialAperture,surface_validation,compare_passages

class ApertureTests(unittest.TestCase):
 def setup_path(self,path):
  q=np.vstack(([[-2.,-2.,0.],[2.,-2.,0.],[2.,2.,0.],[-2.,2.,0.]],path));s=np.arange(len(q),dtype=float)
  return q,s,MaterialAperture.bind(q,s,[0.,3.],[0,0,1])
 def test_shared_diagonal_counted_once_and_sign_reverses(self):
  q,s,a=self.setup_path([[0,0,-1],[0,0,1]])
  r=a.evaluate(q,s,[4,5]);self.assertTrue(r['witness_valid']);self.assertEqual([x['sign']for x in r['crossings']],[1]);self.assertEqual(len(r['crossings'][0]['triangles']),2)
  q[4:]=q[4:][::-1];self.assertEqual(a.evaluate(q,s,[4,5])['crossings'][0]['sign'],-1)
 def test_nonplanar_surface_uses_actual3d_intersection(self):
  q,s,a=self.setup_path([[.5,-.3,-1],[.5,-.3,1]])
  q[:4,2]=[0,.6,0,-.4];r=a.evaluate(q,s,[4,5]);self.assertTrue(r['witness_valid']);self.assertEqual(len(r['crossings']),1);self.assertGreater(r['crossings'][0]['point_mm'][2],.05)
 def test_rigid_rotation_does_not_change_material_crossing(self):
  q,s,a=self.setup_path([[.5,-.3,-1],[.5,-.3,1]]);before=a.evaluate(q,s,[4,5]);R=np.array([[0.,0.,1.],[1.,0.,0.],[0.,1.,0.]])
  after=a.evaluate(q@R.T+[2,3,4],s,[4,5]);self.assertTrue(after['witness_valid']);self.assertAlmostEqual(before['crossings'][0]['material_s_mm'],after['crossings'][0]['material_s_mm'])
 def test_coplanar_tangent_and_interval_endpoint_are_ambiguous(self):
  for path in ([[0,0,-1],[0,0,0],[0,0,-1]],[[-1,0,0],[1,0,0]],[[0,0,-1],[0,0,0]]):
   q,s,a=self.setup_path(path);r=a.evaluate(q,s,[4,len(q)-1]);self.assertFalse(r['witness_valid'],path)
 def test_virtual_closure_margin_does_not_create_a_physical_loop(self):
  q,s,a=self.setup_path([[-1.9,0,-1],[-1.9,0,1]]);r=a.evaluate(q,s,[4,5]);self.assertFalse(r['witness_valid']);self.assertFalse(r['physical_custody_certified']);self.assertFalse(r['virtual_closure']['physical'])
 def test_adjacent_fold_overlap_rejected_even_without_degeneracy(self):
  q,s,a=self.setup_path([[0,0,-1],[0,0,1]]);q[0]=[0,2,0];r=a.evaluate(q,s,[4,5]);self.assertFalse(r['surface']['valid']);self.assertFalse(r['surface']['degenerate_triangles']);self.assertTrue(r['surface']['self_intersections'])
 def test_disjoint_triangle_interior_intersection_rejected(self):
  vertices=np.array([[-2,-2,0],[2,-2,0],[0,2,0],[0,-1,-1],[0,1,-1],[0,0,1]],float)
  r=surface_validation(vertices,np.array([[0,1,2],[3,4,5]]));self.assertFalse(r['valid']);self.assertTrue(r['self_intersections'])
 def test_collinear_boundary_nodes_retained_after_bending(self):
  q=np.array([[-2,-2,0],[0,-2,0],[2,-2,0],[2,2,0],[-2,2,0],[0,0,-1],[0,0,1]],float);s=np.arange(len(q),dtype=float);a=MaterialAperture.bind(q,s,[0,4],[0,0,1]);self.assertEqual(len(a.boundary_s),5)
  q[1,2]=.4;self.assertEqual(a.vertices(q,s)[np.argmin(abs(a.boundary_s-1)),2],.4);self.assertTrue(a.evaluate(q,s,[5,6])['witness_valid'])
 def test_remesh_cannot_hide_a_new_boundary_bend(self):
  q,s,a=self.setup_path([[0,0,-1],[0,0,1]]);q2=np.insert(q,1,(q[0]+q[1])/2,axis=0);s2=np.insert(s,1,.5);np.testing.assert_allclose(a.vertices(q2,s2),a.vertices(q,s));q2[1,2]=.1
  with self.assertRaises(ValueError):a.vertices(q2,s2)
 def test_material_windows_and_global_virtual_closure_separation_required(self):
  q,s,a=self.setup_path([[0,0,-1],[0,0,1]]);r=a.evaluate(q,s,[4,5])
  self.assertTrue(compare_passages(r,[1],material_s_windows=[[4.4,4.6]])['passage_witness_passed'])
  self.assertFalse(compare_passages(r,[1],material_s_windows=[[4.7,4.8]])['passage_witness_passed'])
  self.assertFalse(compare_passages(r,[-1])['passage_witness_passed'])
  r['virtual_closure']['path_separated']=False
  self.assertFalse(compare_passages(r,[1])['passage_witness_passed'])
 def test_invalid_triangle_data_and_material_domain_fail_closed(self):
  q,s,a=self.setup_path([[0,0,-1],[0,0,1]])
  for tri in (np.array([[0.,1.,2.]]),np.array([[0,1,99]])):
   with self.assertRaises(ValueError):surface_validation(q[:4],tri)
  with self.assertRaises(ValueError):MaterialAperture(np.arange(4),np.array([[0,1,2],[0,1,3]]),np.array([0,0,1]))
  with self.assertRaises(ValueError):a.vertices(q,s+1)
if __name__=='__main__':unittest.main()
