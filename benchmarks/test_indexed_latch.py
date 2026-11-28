import importlib.util
import unittest

from examples.indexed_latch import replay, replay_native, replay_brake


class IndexedLatch(unittest.TestCase):
    def test_balanced_cam_load_reversal(self):
        result = replay_brake()
        self.assertAlmostEqual(result['moving_kg'],result['cam_design_kg'],places=11)
        self.assertLess(result['transverse_centroid_error_mm'],1.e-8)
        negative,positive = result['signed_pin_forces_N']
        self.assertAlmostEqual(negative,-.025094759,places=8)
        self.assertGreater(positive,0)
        self.assertAlmostEqual(result['pushrod_fivefold_average_bond_shear_MPa'],.8712127,places=6)

    @unittest.skipUnless(importlib.util.find_spec('cadquery'), 'CadQuery is required to measure native STEP solids')
    def test_conical_seat_and_mass_from_native_solids(self):
        result = replay_brake(native=True)
        self.assertAlmostEqual(result['moving_kg'],result['cam_design_kg'],places=10)
        self.assertLess(result['transverse_centroid_error_mm'],1.e-7)
        for lock in result['locks']:
            self.assertLess(lock['common_mm3'],1.e-9)
            self.assertGreater(min(lock['plus_0p02_deg_mm3'],lock['minus_0p02_deg_mm3']),1.e-5)
            self.assertGreater(lock['released_gap_mm'],.045)
        self.assertGreater(result['folded_rotor_to_yarn_mm'],.015)
        self.assertGreater(result['trimmed_fork_to_yarn_mm'],.00048)

    def test_two_releases_and_index_force(self):
        result = replay()
        near, far = result['releases']
        self.assertEqual((near['loop'],far['loop']),('L1','L0'))
        self.assertAlmostEqual(near['stroke_mm'],3.774357,places=5)
        self.assertAlmostEqual(far['stroke_mm'],23.853044,places=5)
        load = result['load_case']
        self.assertAlmostEqual(load['dog_N'],.0390010143,places=8)
        self.assertLess(load['force_error_N'],1.e-12)
        self.assertLess(load['moment_error_Nmm'],1.e-12)

    @unittest.skipUnless(importlib.util.find_spec('cadquery'), 'CadQuery is required to measure native STEP solids')
    def test_indexed_solid_and_yarn_path(self):
        result = replay_native()
        for lock in result['positive_locks']:
            self.assertLess(lock['gap_mm'],1.e-7)
            self.assertLess(lock['common_volume_mm3'],1.e-9)
            self.assertGreater(lock['overtravel_0p1_deg_mm3'],1.e-6)
        self.assertGreater(result['swivel_yarn_floor_mm'],.070)
        parts = result['withdraw_yarn_floor_mm']
        self.assertGreater(min(parts.values()),.00048)
        self.assertGreater(parts['rotor'],.015)
        self.assertGreater(result['dog_motion_yarn_floor_mm'],.19)
