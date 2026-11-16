import unittest,json,numpy as np
from cad.transfer.build import parts,base,C
from cad.transfer.contact_envelopes import carriage_boxes
from physics.auxiliary_contact import AuxiliaryContact,box_distance3d
class CarriageCover(unittest.TestCase):
 def test_cover_contains_entire_native_carriage_without_filling_access_corridor(self):
  I=json.loads((base.ROOT/'spec/transfer_interfaces.json').read_text());boxes=carriage_boxes(C,I);cover=base.box(*boxes[0])
  for b in boxes[1:]:cover=cover.union(base.box(*b))
  shape=parts()['R05_lift_carriage'].val();self.assertLess(shape.cut(cover.val()).Volume(),1e-6)
  q=np.array([[10.,-6.,0.]])
  spec={'bbox_mm':[2.7256,49,-9,28,-10,10],'boxes_mm':boxes,'motion':'fixed'};d,g=AuxiliaryContact({'carriage':spec}).distance(q)
  self.assertGreater(d[0],.3);self.assertFalse(shape.isInside(tuple(q[0]),1e-7));self.assertLessEqual(d[0],shape.distance(base.cq.Vertex.makeVertex(*q[0]))+1e-7)
  self.assertLess(box_distance3d(q,[2.7256,-9,-10],[49,28,10])[0][0],0)
