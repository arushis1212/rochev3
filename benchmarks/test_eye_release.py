import json
from pathlib import Path
import unittest

from examples.eye_release import crossings, replay


class EyeRelease(unittest.TestCase):
    def test_moving_register(self):
        data = json.loads((Path(__file__).resolve().parents[1]/'cad/castoff/eye_release.json').read_text())
        stations = list(replay(data))
        self.assertEqual([sum(map(len,hits)) for _,hits in stations], [5,4,3,2,1,0,0])
        feeder = data['feeder_replay']
        self.assertAlmostEqual(feeder['payout_mm'], stations[-1][0]['payout_mm'], places=10)
        self.assertEqual(feeder['native_solids_at_stop'], 733)
        self.assertEqual(feeder['consecutive_eye_intervals'], 113)
        self.assertLess(feeder['max_prefix_force_residual_mN'], .001)
        previous = -1
        for row,hits in stations:
            self.assertLess(previous, row['payout_mm'])
            previous = row['payout_mm']
            self.assertEqual(row['crossings'], sum(map(len,hits)))
            self.assertTrue(all(direction == 1 for section in hits for _,direction in section))
            self.assertEqual(row['jaw_mark_mm'],1073.)
            self.assertLess(row['mark_error_mm'],1e-7)
            self.assertGreaterEqual(row['minimum_omitted_box_gap_mm'],.05)
            self.assertLessEqual(row['dynamic_residual_mN'],.001)
            for normal in row['jaw_normals_mN'].values():
                self.assertGreater(normal,0)
                self.assertLess(normal,data['normal_limit_per_face_mN'])

    def test_shared_vertex_and_rectangle(self):
        points = [[0,0,0,-1],[1,0,0,0],[2,0,0,1]]
        edges = list(zip(points,points[1:]))
        self.assertEqual(crossings(edges,0,[-1,1,-1,1]),[(1.,1)])
        self.assertEqual(crossings(edges,0,[1,2,-1,1]),[])
        self.assertEqual(crossings([(b,a) for a,b in edges],0,[-1,1,-1,1]),[(1.,-1)])
