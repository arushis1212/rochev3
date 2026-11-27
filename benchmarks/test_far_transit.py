import unittest
from pathlib import Path
import numpy as np
from examples.material_transit import replay

class FarTransitTests(unittest.TestCase):
    def test_same_start_and_material_on_refinement(self):
        folder=Path(__file__).resolve().parents[1]/'examples'
        cases=[folder/f'receiver_transit_far_{dt}us.npz' for dt in ('25','12p5')]
        with np.load(cases[0]) as a, np.load(cases[1]) as b:
            np.testing.assert_array_equal(a['q_mm'][0],b['q_mm'][0])
            np.testing.assert_array_equal(a['eye_origin_mm'][0],b['eye_origin_mm'][0])
            np.testing.assert_array_equal(a['s_mm'],b['s_mm'])
        event_times=[]
        for path in cases:
            result=replay(path)
            self.assertLess(result['grip_error_mm'],1e-8)
            self.assertLess(result['max_reported_dynamic_residual_uN'],1.)
            l0,l1=(result['loops'][key] for key in ('L0','L1'))
            self.assertFalse(any(l0['paired_at_frames']))
            self.assertEqual(l0['events'],[])
            self.assertFalse(l1['paired_at_frames'][0])
            self.assertTrue(l1['paired_at_frames'][-1])
            event,=l1['events']
            self.assertEqual((event['face'],event['sign']),(2,1))
            self.assertGreater(min(event['barycentric']),.03)
            self.assertTrue(8.<event['time_us']<9.)
            event_times.append(event['time_us'])
        self.assertLess(abs(event_times[0]-event_times[1]),.31)
