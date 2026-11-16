import unittest,json,numpy as np
from pathlib import Path
from physics.auxiliary_contact import box_distance3d,AuxiliaryContact
class AuxiliaryEnvelope(unittest.TestCase):
 def test_signed_box_analytic_distances_and_gradient(self):
  lo=np.array([-1.,-2.,-3.]);hi=-lo;p=np.array([[2.,3.,4.],[0.,0.,0.],[.8,.5,.2]])
  d,g=box_distance3d(p,lo,hi);np.testing.assert_allclose(d,[np.sqrt(3),-1,-.2],atol=1e-12)
  h=1e-6
  for j in range(3):
   a=p[[0,2]].copy();b=a.copy();a[:,j]+=h;b[:,j]-=h
   np.testing.assert_allclose((box_distance3d(a,lo,hi)[0]-box_distance3d(b,lo,hi)[0])/(2*h),g[[0,2],j],atol=1e-9)
 def test_envelopes_cover_all_auxiliary_parts_and_move_with_carriage(self):
  root=Path(__file__).resolve().parents[1];env=json.loads((root/'cad/transfer/generated/auxiliary_envelopes.json').read_text());manifest=json.loads((root/'cad/transfer/generated/manifest.json').read_text())
  expected={n for n in manifest if n.startswith(('R05','R06','R07','R08','R09','R10'))};self.assertEqual(set(env),expected);self.assertEqual(len(expected),9)
  for n,spec in env.items():self.assertEqual(spec['bbox_mm'],manifest[n]['bbox_mm'])
  one={'R05':env['R05_lift_carriage']};p=np.array([[0.,0.,0.],[10.,20.,3.]])
  a=AuxiliaryContact(one,6).distance(p)[0];q=p.copy();q[:,1]-=6
  np.testing.assert_allclose(a,AuxiliaryContact(one,0).distance(q)[0],atol=1e-12)
