import unittest,numpy as np
from physics.auxiliary_contact import box_distance3d
from physics.mesh_path_certificate import certify_interpolation
class SolidBox:
 def distance(self,p):return box_distance3d(p,[-10,-10,-1],[10,10,0])
class MeshPathCertificate(unittest.TestCase):
 def test_safe_lateral_path_needs_temporal_subdivision(self):
  a=np.array([[0.,0.,.4],[0.,1.,.4]]);b=a+np.array([1.2,0,0])
  r=certify_interpolation(a,b,np.array([1.]),.3,SolidBox())
  self.assertTrue(r['certified_centerline_noncrossing']);self.assertGreater(r['subdivisions'],1)
  self.assertGreater(r['solid_bound_mm'],0)
 def test_valid_endpoints_do_not_hide_intermediate_solid_crossing(self):
  a=np.array([[0.,0.,.4],[0.,1.,.4]]);b=a.copy();b[:,2]=-1.4
  r=certify_interpolation(a,b,np.array([1.]),.3,SolidBox())
  self.assertFalse(r['certified_centerline_noncrossing']);self.assertLess(r['solid_bound_mm'],0)
