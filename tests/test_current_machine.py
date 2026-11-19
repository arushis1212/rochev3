"""Current composition and query-boundary regressions, not stitch qualification."""
import unittest
from unittest.mock import patch
import numpy as np


class NativeQueryBoundary(unittest.TestCase):
    def test_native_overlap_distinguishes_contact_from_volume(self):
        import cadquery as cq
        from physics.native_overlap import overlap_pairs
        a = cq.Workplane('XY').box(2,2,2).val()
        touching = a.translate((2,0,0))
        penetrating = a.translate((1.5,0,0))
        self.assertEqual(overlap_pairs({'a':a,'touching':touching}), [])
        rows = overlap_pairs({'a':a,'penetrating':penetrating})
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]['intersection_mm3'], 2, places=8)
        with self.assertRaises(ValueError):
            overlap_pairs({'a':a}, float('nan'))

    def test_invalid_material_or_pose_cannot_be_reported_clear(self):
        from physics.feed_native import upstream_clearance
        valid = np.array([[0., 0., 0.], [1., 0., 0.]])
        with patch('physics.feed_native.hardware', side_effect=AssertionError('must reject before CAD')):
            for q in (np.empty((0, 3)), np.zeros((1, 3)), [[0, 0], [1, 1]], [[0, 0, 0], [1, float('nan'), 0]]):
                with self.assertRaises(ValueError):
                    upstream_clearance(q, [0, 0, 0, 0], [0, 0, 0])
            for radius in (0, -.3, float('nan'), float('inf')):
                with self.assertRaises(ValueError):
                    upstream_clearance(valid, [0, 0, 0, 0], [0, 0, 0], radius=radius)
            for kw in ({'mode':'unknown'}, {'z':float('nan')}, {'edge_offset':True}):
                with self.assertRaises(ValueError):
                    upstream_clearance(valid, [0, 0, 0, 0], [0, 0, 0], **kw)


class CurrentMachineComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cad.machine import assembly
        cls.machine = assembly
        cls.scene = assembly.inventory_scene()

    def test_one_base_contains_both_real_mounting_patterns(self):
        from cad.r5m2 import service, build
        from cad.transfer import indexed
        shape = self.scene['F03_base_board']
        self.assertTrue(shape.isValid())
        self.assertEqual(len(shape.Solids()), 1)
        # A clearance gauge must actually pass through both module hole sets.
        ports = indexed.board_ports() + service.C['base_holes_xy_mm']
        for x, y in ports:
            gauge = build.cyl_z(-.1, build.S['frame']['base_size'][2]+.1, 1.69, x, y).val()
            self.assertLess(shape.intersect(gauge).Volume(), 1e-8)

    def test_current_scene_has_real_service_and_no_superseded_bracket(self):
        self.assertNotIn('M01_frame_bracket', self.scene)
        for name in ('P01_tower','P10_fairlead_bracket','P13_nip_lower','P14_nip_upper','P15_pad_lower','P15_pad_upper'):
            self.assertNotIn(name, self.scene)
        for name in ('NIP_NS02_tower_keyed','NIP_NS06_lower_pad_IN','NIP_NS06_lower_pad_OUT',
                     'XT01_crossbeam','XT12_index_pin','SERVICE_CS01_upright'):
            self.assertIn(name, self.scene)
        self.assertTrue(all(shape.isValid() and len(shape.Solids()) == 1 for shape in self.scene.values()))

    def test_main_roll_and_transfer_dock_are_independent_physical_controls(self):
        from cad.transfer import indexed
        from cad.r5m2 import build
        a = self.machine.installed(head_roll=0, transfer_x=indexed.S['park_x_mm'])
        b = self.machine.installed(head_roll=120, transfer_x=indexed.S['park_x_mm'])
        self.assertLess(abs(a['TRANSFER_R01_front_stripper'].intersect(b['TRANSFER_R01_front_stripper']).Volume()
                            - a['TRANSFER_R01_front_stripper'].Volume()), 1e-7)
        self.assertLess(a['TOOL_H01_hook_body'].intersect(b['TOOL_H01_hook_body']).Volume(),
                        a['TOOL_H01_hook_body'].Volume()-.01)
        raised = self.machine.installed(transfer_x=indexed.S['park_x_mm'], dock_height=30)
        lo, hi = a['TRANSFER_R01_front_stripper'].BoundingBox(), raised['TRANSFER_R01_front_stripper'].BoundingBox()
        self.assertAlmostEqual(hi.zmin-lo.zmin, 30, places=7)
        self.assertFalse(build.joint_limit_violations(
            indexed.original.I['reference_tip_xyz_mm'], indexed.S['guide_index_park_mm']))
        with self.assertRaises(ValueError):
            self.machine.installed(dock_height=15)
        with self.assertRaises(ValueError):
            self.machine.installed(cradle_position='HIGH_RELEASE', cradle_indexed=True)


if __name__ == '__main__':
    unittest.main()
