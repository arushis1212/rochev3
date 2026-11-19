import unittest,json
from pathlib import Path
import numpy as np
from physics.transfer_holding import WorldTransfer
from physics.guide_contact import GuidedContact
from physics.loop_holding import head_frame
from physics.roche_contact3d import contact_energy3d
ROOT=Path(__file__).resolve().parents[1]
class Dense:
 def __init__(self,o):self.o=o
 def contact_components(self,p,r):return self.o.contact_components(p,r)
class SparseContactTests(unittest.TestCase):
 def test_all_active_terms_and_gradients_equal_dense(self):
  cfg=json.loads((ROOT/'spec/transfer_holding.json').read_text());s=json.loads((ROOT/'spec/connected_yarn.json').read_text());profiles=json.loads((ROOT/'cad/transfer/generated/contact_profiles.json').read_text());base=json.loads((ROOT/'cad/r5m2/generated/contact_profiles.json').read_text())['profiles'];full=json.loads((ROOT/'spec/r5_m2_fixture.json').read_text());o,M=head_frame(cfg['head_tip_xyz_mm']);guide=o+M@np.array(s['guide_local_mm']);data=json.loads((ROOT/'tests/fixtures/contact_reference.json').read_text());q=np.array(data['q']);rest=np.array(data['rest']);rng=np.random.default_rng(23)
  for state in [[6.285714285714286,0,6,0],[-8.5,0,0,6],[0,16.5,0,0]]:
   ob=GuidedContact(WorldTransfer(profiles,base,cfg['head_tip_xyz_mm'],*state),guide,full['guide'])
   for points in [q,q+rng.normal(0,.1,q.shape)]:
    e,g=contact_energy3d(points,rest,.3,1000,ob,32);f,h=contact_energy3d(points,rest,.3,1000,Dense(ob),32);self.assertAlmostEqual(e,f,places=10);np.testing.assert_allclose(g,h,rtol=1e-12,atol=1e-10)
   points=o+rng.uniform([-40,-60,-50],[70,80,50],(500,3))@M.T;full_terms=ob.contact_components(points,.3);dense=sum((np.maximum(.3-d,0)[:,None]*g for d,g in full_terms),np.zeros_like(points));sparse=np.zeros_like(points)
   for idx,d,g in ob.sparse_components(points,.3):sparse[idx]+=np.maximum(.3-d,0)[:,None]*g
   np.testing.assert_allclose(sparse,dense,rtol=1e-12,atol=1e-10)
