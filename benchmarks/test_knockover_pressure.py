import json
import unittest
from pathlib import Path

from physics.plane_yarn_pressure import segment_pressure


class KnockoverPressure(unittest.TestCase):
    def test_against_installed_plate(self):
        path=Path(__file__).resolve().parents[1]/"examples/knockover_pressure.json"
        case=json.loads(path.read_bytes())
        for sample in case["samples"]:
            for i,rest in enumerate(case["stress_free_lengths_mm"]):
                a,b=sample["points_mm"][i:i+2]
                _,F=segment_pressure(a,b,case["face_point_mm"],case["outward_unit_normal"],
                                     case["yarn_radius_mm"],rest,case["normal_stiffness_N_per_mm2"])
                self.assertAlmostEqual(sum(f[1] for f in F),sample["native_reaction_Y_N"][i],delta=1e-11)

    def test_half_loaded_triangle(self):
        e,force=segment_pressure((0,0,0),(3,2,0),(0,0,0),(0,1,0),1,4,3)
        self.assertAlmostEqual(e,1.)
        self.assertAlmostEqual(force[0][1],2.5)
        self.assertAlmostEqual(force[1][1],.5)

    def test_node_reversal_and_work(self):
        a,b=(1.,.12,0.),(3.,.52,.1)
        args=((0,0,0),(0,1,0),.3,4.,125.)
        e,forces=segment_pressure(a,b,*args)
        flipped,reversed_forces=segment_pressure(b,a,*args)
        self.assertAlmostEqual(e,flipped)
        self.assertAlmostEqual(forces[0][1],reversed_forces[1][1])
        delta=1e-6
        above=(a[0],a[1]+delta,a[2])
        below=(a[0],a[1]-delta,a[2])
        derivative=(segment_pressure(above,b,*args)[0]-segment_pressure(below,b,*args)[0])/(2*delta)
        self.assertAlmostEqual(-derivative,forces[0][1],delta=5e-8)

    def test_full_partial_and_zero_contact(self):
        args=((0,0,0),(0,1,0),.5,2.,10.)
        e,(a,b)=segment_pressure((0,.25,0),(1,.25,0),*args)
        self.assertAlmostEqual(e,.625)
        self.assertEqual(a,b)
        self.assertEqual(a,(0.,2.5,0.))
        self.assertEqual(segment_pressure((0,.51,0),(1,.6,0),*args)[0],0.)
