import unittest
from pathlib import Path
import numpy as np
from examples.loaded_feeder import replay, score

class LoadedFeederTests(unittest.TestCase):
    def setUp(self):
        self.path=Path(__file__).resolve().parents[1]/'examples/loaded_feeder.npz'

    def test_reactions_and_rest_length(self):
        stops=replay(self.path)
        self.assertEqual(len(stops),5)
        for stop in stops:
            self.assertAlmostEqual(stop['out_mark_mm']-stops[0]['out_mark_mm'],stop['issued_mm'],places=8)
            self.assertEqual(stop['in_mark_mm'],stops[0]['in_mark_mm'])
            self.assertLess(stop['free_yarn_residual_N'],1e-6)
            self.assertLess(stop['carriage_residual_N'],1e-6)
            self.assertLess(stop['largest_active_gap_mm'],1e-7)
        self.assertTrue(all(a['height_mm']<b['height_mm'] for a,b in zip(stops,stops[1:])))

    def test_removed_moving_pulley_support(self):
        with np.load(self.path) as archive:
            data=dict(archive)
        data['normal_N']=data['normal_N'].copy()
        data['normal_N'][0,2]=0.
        self.assertAlmostEqual(score(data,0)['carriage_residual_N'],float(data['carriage_weight_N']),places=10)
