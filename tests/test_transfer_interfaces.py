import unittest
from cad.transfer.build import parts

class ActualTravelStops(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.parts=parts()
 def test_gate_slot_and_sleeve_enforce_declared_travel(self):
  barrel=self.parts['TH_H03_barrel_stop'].val();sleeve=self.parts['TH_H08_stop_sleeve'].val()
  for q in [0.,8.25,16.5]:self.assertLess(barrel.intersect(sleeve.translate((-q,0,0))).Volume(),1e-7)
  for q in [-.01,16.51]:self.assertGreater(barrel.intersect(sleeve.translate((-q,0,0))).Volume(),1e-7)
 def test_lift_slot_and_sleeve_enforce_declared_travel(self):
  sleeve=self.parts['R11_lift_stop_sleeve'].val();carrier=self.parts['R05_lift_carriage'].val()
  for q in [0.,3.,6.]:self.assertLess(sleeve.intersect(carrier.translate((0,q,0))).Volume(),1e-7)
  for q in [-.01,6.01]:self.assertGreater(sleeve.intersect(carrier.translate((0,q,0))).Volume(),1e-7)
