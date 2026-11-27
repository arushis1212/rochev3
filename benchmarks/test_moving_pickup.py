import unittest

from examples.moving_pickup import replay


class MovingPickupTests(unittest.TestCase):
    def test_open_at_transfer_then_traps_the_registered_fresh_strand(self):
        result = replay()
        self.assertEqual(result['sections'], 5)
        self.assertAlmostEqual(result['end_ms'], 7.173673, places=5)
        self.assertGreaterEqual(result['frames'], 450)
        self.assertGreater(result['material_mm'][0], 1055.)
        self.assertTrue(result['at_receiver_contact']['open_path'])
        self.assertTrue(result['terminal']['trapped'])
