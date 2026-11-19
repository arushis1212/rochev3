import unittest,json
from pathlib import Path
import numpy as np
from physics.edge_contact import edge_samples
from physics.roche_contact3d import contact_energy3d
from tests.test_sparse_contact import Dense
from physics.transfer_holding import WorldTransfer
from physics.guide_contact import GuidedContact
from physics.loop_holding import head_frame,contact_counts
ROOT=Path(__file__).resolve().parents[1]
class EdgeContactTests(unittest.TestCase):
 def test_slab_selection_equals_brute_midpoints_including_parallel(self):
  rng=np.random.default_rng(44);q=rng.uniform(-4,4,(80,3));q[1,:]=q[0,:];q[3,0]=q[2,0];rest=np.ones(79);counts=np.arange(79)%23+1;lo=np.array([-1,-2,-1]);hi=np.array([1,2,1]);r=.3
  e,t,w,p=edge_samples(q,rest,counts,lo,hi,r);got={(int(i),round(float(v),13))for i,v in zip(e,t)};expected=set()
  for i,n in enumerate(counts):
   for k in range(n):
    u=(k+.5)/n;x=(1-u)*q[i]+u*q[i+1]
    if np.all(x>=lo-r)&np.all(x<=hi+r):expected.add((i,round(u,13)))
  self.assertEqual(got,expected)
 def test_fine_contact_energy_force_equivalent_to_dense(self):
  cfg=json.loads((ROOT/'spec/transfer_holding.json').read_text());s=json.loads((ROOT/'spec/connected_yarn.json').read_text());profiles=json.loads((ROOT/'cad/transfer/generated/contact_profiles.json').read_text());base=json.loads((ROOT/'cad/r5m2/generated/contact_profiles.json').read_text())['profiles'];full=json.loads((ROOT/'spec/r5_m2_fixture.json').read_text());o,M=head_frame(cfg['head_tip_xyz_mm']);guide=o+M@np.array(s['guide_local_mm']);data=json.loads((ROOT/'tests/fixtures/contact_reference.json').read_text());q=np.array(data['q']);rest=np.array(data['rest']);rng=np.random.default_rng(25)
  for state in [[6.285714285714286,0,6,0],[-8.5,0,0,6],[0,16.5,0,0]]:
   ob=GuidedContact(WorldTransfer(profiles,base,cfg['head_tip_xyz_mm'],*state),guide,full['guide'])
   for points in [q,q+rng.normal(0,.1,q.shape)]:
    e,g=contact_energy3d(points,rest,.3,1000,ob,contact_counts(rest,{**cfg,'contact_reference_spacing_mm':.0125}));f,h=contact_energy3d(points,rest,.3,1000,Dense(ob),contact_counts(rest,{**cfg,'contact_reference_spacing_mm':.0125}));self.assertAlmostEqual(e,f,places=8);np.testing.assert_allclose(g,h,rtol=1e-10,atol=1e-9)
