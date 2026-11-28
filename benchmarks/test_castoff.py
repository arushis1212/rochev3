import unittest

from examples.castoff import replay


class CastoffReplay(unittest.TestCase):
    def test_fork_releases_and_pin_enclosure(self):
        result=replay()
        self.assertEqual([row['loop'] for row in result['releases']],['L1','L0'])
        near,far=result['releases']
        self.assertAlmostEqual(near['withdrawal_mm'],4.110954074,places=6)
        self.assertAlmostEqual(far['withdrawal_mm'],23.831231836,places=6)
        self.assertLess(far['withdrawal_mm'],result['stroke_mm'])
        self.assertAlmostEqual(result['required_loop_width_mm'],9.1,places=6)
        self.assertAlmostEqual(result['minimum_loop_perimeter_mm'],21.053981634,places=6)
