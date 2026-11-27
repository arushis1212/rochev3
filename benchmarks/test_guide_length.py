import json
import math
from pathlib import Path
import unittest
from examples.guide_length import disk_distance, length_bound
from examples.parked_mouth import parked_mouth


class GuideTravelTests(unittest.TestCase):
    def test_parked_mouth_minimum_feed(self):
        reach, span, slide = parked_mouth()
        self.assertAlmostEqual(reach, 46.92145314, places=7)
        self.assertAlmostEqual(span, 33.1805166, places=7)
        self.assertAlmostEqual(slide, reach-span, places=12)

    def test_axial_and_outside_disk(self):
        self.assertEqual(2,disk_distance((0,0,-2),(0,0,0),(0,0,5),3))
        self.assertEqual(5,disk_distance((5,0,4),(0,0,0),(0,0,1),2))

    def test_straight_line_crosses_the_bore(self):
        ends=[(-2,0,-2),(2,0,2)]
        self.assertAlmostEqual(math.dist(*ends),length_bound(ends,(0,0,0),(0,0,1),1,.01))

    def test_bound_holds_for_sampled_crossings_and_translations(self):
        anchors=[(1,4,-2),(-4,3,2)]
        bound=length_bound(anchors,(0,0,0),(0,0,1),1,.2)
        for ang in range(0,360,15):
            for r in (0,.5,1):
                for shift in (-.2,.2):
                    p=(r*math.cos(math.radians(ang))+shift,r*math.sin(math.radians(ang)),0)
                    self.assertLessEqual(bound,sum(math.dist(a,p) for a in anchors)+1e-12)

    def test_worked_withdrawal(self):
        p=Path(__file__).resolve().parents[1]/"examples"/"guide_travel.json"
        a=json.loads(p.read_text())
        bound=length_bound(a["anchors"],a["disk_center_end"],a["normal"],a["inner_radius"],a["position_uncertainty"],a["roundoff_reserve"])
        self.assertAlmostEqual(bound-a["rest_length"],4.828114317,places=8)

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):
            disk_distance((0,0,0),(0,0,0),(0,0,0),1)
        with self.assertRaises(ValueError):
            length_bound([(0,0,0)],(0,0,0),(0,0,1),1)


if __name__=="__main__":
    unittest.main()
