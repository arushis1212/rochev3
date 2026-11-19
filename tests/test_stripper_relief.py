import unittest
import cadquery as cq
from cad.transfer.build import parts,C,T
class StripperReliefTests(unittest.TestCase):
 def test_working_strand_corridor_and_upper_retention_and_ligament(self):
  ps=parts()
  for name,u in [('R01_front_stripper',1.5),('R02_rear_stripper',-1.5)]:
   shape=ps[name].val();p=cq.Vector(u,.2,T['body_thickness']/2+.3)
   self.assertFalse(shape.isInside(p,1e-8));distance=min(f.distance(cq.Vertex.makeVertex(*p.toTuple()))for f in shape.Faces())
   self.assertAlmostEqual(distance,C['stripper_lower_relief_halfwidth_mm']-T['body_thickness']/2-.3,places=7)
   self.assertGreater(distance,.3)
   self.assertTrue(shape.isInside(cq.Vector(u,6,1.3),1e-8))
   ligament_mid=(C['stripper_lower_relief_halfwidth_mm']+C['lift_pin_w_mm']-C['lift_pin_radius_mm']-C['lift_slot_clearance_mm'])/2
   self.assertTrue(shape.isInside(cq.Vector(u,.2,ligament_mid),1e-8))
   self.assertTrue(shape.isValid());self.assertEqual(len(shape.Solids()),1)
