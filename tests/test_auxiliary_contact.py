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
  modeled={'H01_hook_body','H02_gate','H02_contact_blade','R01_front_stripper','R02_rear_stripper','R03_lift_pin_0','R03_lift_pin_1'}
  expected=set(manifest)-modeled;self.assertEqual(set(env),expected);self.assertEqual(len(expected),40)
  for n,spec in env.items():self.assertEqual(spec['bbox_mm'],manifest[n]['bbox_mm'])
  one={'R05':env['R05_lift_carriage']};p=np.array([[0.,0.,0.],[10.,20.,3.]])
  a=AuxiliaryContact(one,6).distance(p)[0];q=p.copy();q[:,1]-=6
  np.testing.assert_allclose(a,AuxiliaryContact(one,0).distance(q)[0],atol=1e-12)
  for name,shift in [('TH_H03_barrel_stop',8.75),('TH_H07_gate_knob',8.75-16.5)]:
   one={name:env[name]};q=p.copy();q[:,0]-=shift
   np.testing.assert_allclose(AuxiliaryContact(one,6,8.75,16.5).distance(p)[0],AuxiliaryContact(one).distance(q)[0],atol=1e-12)
