import unittest
import numpy as np
from cad.r5m2 import build as cad
from physics.r5_feeder import mass_budget
from physics.nip_grip import NipGrip
from physics.feeder_domain import NipPads

class D26PeripheralsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.parts=cad.peripherals.parts(cad);cls.scene={};cad.peripherals.add(cls.scene,cls.parts,cad)
 def test_flat_head_is_seated_without_jaw_penetration_and_rear_remains_plain(self):
  a=self.scene['D01_jaw_A'];b=self.scene['D01_jaw_B']
  self.assertLess(a.Volume(),b.Volume())
  for i in range(4):
   screw=self.scene[f'HW_M3x16_cloth_{i}'];bb=screw.BoundingBox()
   self.assertLess(screw.intersect(a).Volume(),1e-7)
   self.assertGreaterEqual(bb.ymin,a.BoundingBox().ymin-1e-7)
   self.assertAlmostEqual(bb.ymax-bb.ymin,16.,places=6)
   nut=self.scene[f'HW_M3nut_cloth_{i}'];self.assertGreater(bb.ymax-nut.BoundingBox().ymax,3.)
 def test_rod_clearance_and_bearing_fit_are_positive_bounded_stacks(self):
  f=cad.S['feeder'];self.assertAlmostEqual(self.parts['P20_rod'].val().BoundingBox().zlen,87.7)
  self.assertGreater((204-.05)-(116+.05)-(87.7+.05),.1499)
  lo,hi=f['finished_interfaces']['bearing_local_od_mm'];d=f['pulley_bearing_pocket_diameter_mm'];t=f['pulley_bearing_pocket_tolerance_mm']
  self.assertAlmostEqual(lo-d-t,.007);self.assertAlmostEqual(hi-d+t,.025)
 def test_longer_pulley_screws_in_mass_and_native_tip(self):
  result=mass_budget(cad,self.parts);self.assertTrue(result['mass_screen_pass'])
  self.assertGreater(result['ballast_margin_g'],.05)
  self.assertIn('M2x10',[r['part']for r in result['components']])
  for name,obj in self.scene.items():
   if name.startswith('HW_M2x10_pulley'):self.assertAlmostEqual(obj.BoundingBox().ymin,399.,places=6)
 def test_closed_nip_compression_requires_bounded_declared_material(self):
  feeder=cad.S['feeder'];section={'indices':[2,3,4],'world_xyz_mm':[[22.1,406,238.75],[20,406,238.75],[16,406,238.75]]}
  grip=NipGrip(feeder,section,5);pads=NipPads(feeder);pads.set_grip(grip)
  point=np.array([[20.,406.,238.75]])
  self.assertLess(pads.distance_for_edges(point,np.array([0]))[0][0],.3)
  self.assertGreaterEqual(pads.distance_for_edges(point,np.array([2]))[0][0],.349999)
  self.assertLess(pads.distance_for_edges(point,np.array([1]))[0][0],.3)
  # The adjacent strand is not allowed to pass through the pad beside the lane.
  self.assertLess(pads.distance_for_edges(np.array([[20.,407.,238.25]]),np.array([2]))[0][0],0.)
  bad={'indices':[1,3,4],'world_xyz_mm':section['world_xyz_mm']}
  with self.assertRaises(ValueError):NipGrip(feeder,bad,5)
 def test_integer_box_minus_fractional_cut_preserves_volume(self):
  from physics.fixture_contact import subtract_box
  pieces=subtract_box(([0,0,0],[2,2,2]),([.25,.5,.75],[1.25,1.5,1.75]))
  self.assertAlmostEqual(sum(np.prod(hi-lo)for lo,hi in pieces),7.)
  for lo,hi in pieces:
   overlap=np.minimum(hi,[1.25,1.5,1.75])-np.maximum(lo,[.25,.5,.75])
   self.assertFalse(np.all(overlap>1e-10))

if __name__=='__main__':unittest.main()
