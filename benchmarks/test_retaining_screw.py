from dataclasses import replace
import math
import unittest
from examples.retaining_screw import Joint


class RetainingScrew(unittest.TestCase):
    def setUp(self):
        self.case=Joint(24,25,.8,1.2,.1,1.6,2.5,.35,.25,.1)

    def test_both_limiting_equalities(self):
        limits=self.case.diameter_interval_mm()
        self.assertTrue(limits["feasible"])
        area=math.pi*((limits["minimum_diameter_mm"]/2-.1)**2-1.2**2)
        self.assertAlmostEqual(24/(.8*area),25)
        self.assertAlmostEqual(2.5-limits["maximum_diameter_mm"]/2-.35-.25,.1)

    def test_bearing_land_and_yarn_are_independent_limits(self):
        for change in ({"supported_outer_radius_mm":1.25},{"path_to_axis_mm":1.8}):
            with self.subTest(change=change):
                self.assertFalse(replace(self.case,**change).diameter_interval_mm()["feasible"])

    def test_tolerance_and_load(self):
        base=self.case.diameter_interval_mm()
        end=replace(self.case,relative_position_error_mm=.45).diameter_interval_mm()
        self.assertAlmostEqual(base["maximum_diameter_mm"]-end["maximum_diameter_mm"],.4)
        higher=replace(self.case,load_N=36).diameter_interval_mm()
        self.assertGreater(higher["minimum_diameter_mm"],base["minimum_diameter_mm"])

    def test_invalid_parameters(self):
        for k,v in (("load_N",-1),("bearing_limit_MPa",0),("imprint_fraction",1.1),
                    ("inner_land_radius_mm",float("nan"))):
            with self.subTest(parameter=k),self.assertRaises(ValueError):
                replace(self.case,**{k:v}).diameter_interval_mm()
