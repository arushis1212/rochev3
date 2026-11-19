import unittest,json
from pathlib import Path
import numpy as np
from physics.feeder_domain import feeder_potential,Pulley,Fairlead,upstream_route
from physics.roche_contact3d import contact_energy3d
ROOT=Path(__file__).resolve().parents[1]
class FeederDomainTests(unittest.TestCase):
 def test_fairlead_matches_independent_native_solid(self):
  from cad.r5m2 import build as base
  from cad.r5m2 import peripherals
  shape=peripherals.parts(base)['P11_fairlead'].val();q=np.array([[102.,406,238],[107.1,406,238],[102,409.3,238],[108,407,238]])
  d,g=Fairlead().distance(q)
  for p,dist in zip(q,d):self.assertAlmostEqual(dist,shape.distance(base.cq.Vertex.makeVertex(*p)),places=8)
 def test_counterweight_virtual_work_and_stops(self):
  f=json.loads((ROOT/'spec/r5_m2_fixture.json').read_text())['feeder']
  for z in [131,160,189]:
   V,g,zc=feeder_potential(z,f);h=1e-3;fd=(feeder_potential(z+h,f)[0]-feeder_potential(z-h,f)[0])/(2*h);self.assertAlmostEqual(g,fd,places=9)
  for z in [130,190]:
   with self.assertRaises(ValueError):feeder_potential(z,f)
 def test_moving_pulley_contact_action_reaction(self):
  ob=Pulley(48,160);q=np.array([[48.,406.,168.1],[49.,406.,168.1]]);rest=np.array([1.]);E,g=contact_energy3d(q,rest,.3,1000,ob,32);h=1e-5
  ob.moving=False;ob.center[2]+=h;ep=contact_energy3d(q,rest,.3,1000,ob,32)[0];ob.center[2]-=2*h;em=contact_energy3d(q,rest,.3,1000,ob,32)[0];self.assertAlmostEqual((ep-em)/(2*h),-g[:,2].sum(),places=6)
