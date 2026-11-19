import unittest,json
from pathlib import Path
import numpy as np
from physics.analytic_profile import wire_distance
from physics.compiled_profile import prepare_wire,prepare_profile
from physics.roche_contact3d import extrusion_distance

class CompiledProfile(unittest.TestCase):
 def test_all_actual_profiles_against_reference(self):
  root=Path(__file__).resolve().parents[1];rng=np.random.default_rng(139)
  profiles=json.loads((root/'cad/transfer/generated/contact_profiles.json').read_text())
  for p in profiles.values():
   for wire in [p['outer'],*p['holes']]:
    prepared=prepare_wire(wire);vertices=np.array(wire['points']);lo=vertices.min(axis=0)-1;hi=vertices.max(axis=0)+1
    points=rng.uniform(lo,hi,(500,2));a=wire_distance(points,wire);b=wire_distance(points,prepared)
    np.testing.assert_allclose(a[0],b[0],atol=1e-10,rtol=1e-10);np.testing.assert_allclose(a[1],b[1],atol=1e-8,rtol=1e-8)
    for shift in [0.,1e-8,-1e-8]:np.testing.assert_allclose(wire_distance(vertices+shift,wire)[0],wire_distance(vertices+shift,prepared)[0],atol=1e-10,rtol=1e-10)
   points=rng.uniform([-10,-14,-12],[12,26,12],(300,3));a=extrusion_distance(points,p);b=extrusion_distance(points,prepare_profile(p))
   for x,y in zip(a,b):np.testing.assert_allclose(x,y,atol=1e-8,rtol=1e-8)
 def test_prepared_snapshot_does_not_alias_caller_geometry(self):
  wire={'points':[[0.,0.],[1.,0.],[1.,1.],[0.,1.]]};prepared=prepare_wire(wire);wire['points'][1][0]=100.
  self.assertEqual(prepared['points'][1][0],1.)
  np.testing.assert_allclose(wire_distance(np.array([[.5,.5],[2.,.5]]),prepared)[0],[-.5,1.])
