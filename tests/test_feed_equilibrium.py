import unittest,json,numpy as np
from pathlib import Path
from physics.feed_equilibrium import FeedEquilibrium
from physics.feeder_domain import FeederContact
from physics.moving_path_certificate import certify_moving_path

class Empty:
 def edge_contact_terms(self,*args):return iter(())
 def distance(self,p):return np.full(len(p),1e6),np.zeros_like(p)

class FeedEnergyTests(unittest.TestCase):
 def test_full_clamp_rod_feeder_gradient(self):
  root=Path(__file__).resolve().parents[1];cfg=json.loads((root/'spec/transfer_holding.json').read_text());cfg.update(contact_reference_spacing_mm=.5,yarn_linear_density_g_per_m=.1786);feeder=json.loads((root/'spec/r5_m2_fixture.json').read_text())['feeder']
  q=np.array([[26.,400,170],[34,397,171],[42,400,170],[48,406,151.9],[55,406,156],[64,406,238.8]]);rest=np.linalg.norm(np.diff(q,axis=0),axis=1)*.99
  model=FeedEquilibrium(q,rest,2,[48,400,170],[0,0],160,cfg,FeederContact(Empty(),160),feeder,'LOW');x=model.x0;E,g=model.energy(x);fd=[];h=1e-5
  for j in range(len(x)):
   a=x.copy();b=x.copy();a[j]+=h;b[j]-=h;fd.append((model.energy(a)[0]-model.energy(b)[0])/(2*h))
  np.testing.assert_allclose(g,fd,rtol=2e-5,atol=1e-5)
 def test_feeder_displacement_is_included_in_motion_bound(self):
  class Wall:
   def __init__(self,s):self.x=s[4]-1
   def distance(self,p):
    g=np.zeros_like(p);g[:,0]=np.sign(p[:,0]-self.x);return abs(p[:,0]-self.x)-.1,g
  q=np.array([[0.,0,0],[0,1,0]]);args=(q,q,[0,0,0,0,0],[0,0,0,0,2],np.array([1.]),.01,Wall)
  result=certify_moving_path(*args,max_subdivisions=1,spatial_spacing=.1,additional_rigid_motion_mm=2.)
  self.assertFalse(result['certified']);self.assertEqual(result['max_rigid_motion_mm'],2.)
