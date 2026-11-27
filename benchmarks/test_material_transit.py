import unittest
from pathlib import Path
import numpy as np
from examples.material_transit import replay, transit

class MaterialTransit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = Path(__file__).resolve().parents[1] / 'examples'
        cls.runs = [replay(data / name) for name in ('receiver_transit_25us.npz','receiver_transit_12p5us.npz')]

    def test_material_custody(self):
        for run in self.runs:
            self.assertLess(run['grip_error_mm'], 1e-8)
            self.assertAlmostEqual(run['mark_mm'],1076.726604922,places=8)
            self.assertLess(run['max_reported_dynamic_residual_uN'],1.)

    def test_time_refinement(self):
        times = []
        for run in self.runs:
            near, far = (run['loops'][key] for key in ('L0','L1'))
            self.assertFalse(near['paired_at_frames'][0])
            self.assertTrue(near['paired_at_frames'][-1])
            self.assertTrue(all(far['paired_at_frames']))
            self.assertEqual(len(near['events']),1)
            self.assertEqual(far['events'],[])
            hit = near['events'][0]
            self.assertEqual(hit['face'],139)
            self.assertEqual(hit['sign'],1)
            self.assertGreater(min(hit['barycentric']),.2)
            times.append(hit['time_us'])
        self.assertLess(abs(times[0]-times[1]),.5)
        self.assertTrue(all(19 < t < 21 for t in times))

    def test_moving_plane_crosses_stationary_point(self):
        face = np.array([[-1.,-1.,1.],[1.,-1.,1.],[0.,1.,1.]])
        point = np.zeros(3)
        hit, = transit(point,point,face,face-[0.,0.,4.],np.array([[0,1,2]]))
        self.assertAlmostEqual(hit['fraction'],.25)
        self.assertEqual(hit['sign'],1)
