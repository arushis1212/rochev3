import unittest,numpy as np
from cad.transfer import installation as install
from physics.feeder_domain import ScrewCover

class FeedMount(unittest.TestCase):
 def test_screw_engagement_clearance_and_native_cover(self):
  I=install.I;b=install.base;L=I['fairlead_mount_screw_length_mm'];at=I['fairlead_mount_screw_underhead_xyz_mm'];fast=b.S['fasteners']['M3']
  bolt=b.place(b.bolt(3,L),at,(1,0,0),(0,1,0));nut=b.place(b.nut(3),(78,410,238),(1,0,0),(0,1,0));nb=nut.BoundingBox();tip=at[1]-L
  self.assertLess(tip,nb.ymin);self.assertGreater(at[1],nb.ymax)
  edge=b.cq.Edge.makeLine(b.cq.Vector(70,406,238),b.cq.Vector(90,406,238));self.assertGreaterEqual(bolt.distance(edge)-.3,1.7-1e-9)
  cover=ScrewCover(at,L,3,fast['head_d_max'],fast['head_height_max']);solids=[]
  for lo,hi in cover.boxes:solids.append(b.box(lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]))
  union=solids[0].union(solids[1]);self.assertLess(bolt.cut(union.val()).Volume(),1e-7)
  q=np.array([[78.,406,238],[80.,420,238]]);d,_=cover.distance(q)
  for p,dist in zip(q,d):self.assertLessEqual(dist,bolt.distance(b.cq.Vertex.makeVertex(*p))+1e-8)
