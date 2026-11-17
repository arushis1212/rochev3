"""Physical service hardware checks, not a full-machine or textile pass."""
from collections import Counter
import math
import unittest

from cad.r5m2 import service
from physics.native_overlap import overlap_pairs


class CounterweightServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = service
        cls.parts = service.parts()

    def test_component_solids_are_valid_and_inventory_is_complete(self):
        for name, part in self.parts.items():
            self.assertTrue(part.val().isValid(), name)
            self.assertEqual(len(part.solids().vals()), 1, name)
            self.assertGreater(part.val().Volume(), 0, name)
        counts = Counter(row['part_id'] for row in self.c.inventory())
        self.assertEqual(counts, {k: v['quantity'] for k, v in self.c.S['parts'].items()})

    def test_both_supported_positions_have_no_native_interpenetration(self):
        for z in self.c.C['center_stops_mm'].values():
            self.assertEqual(overlap_pairs(self.c.installed(z)), [], z)

    def test_cup_sits_on_real_tray_and_clears_ring(self):
        c = self.c
        for z in c.C['center_stops_mm'].values():
            scene = c.installed(z)
            cup = c.base.cyl_z(z - 12.5, z + 12.5, 6.1, 96, 406).val()
            for name, solid in scene.items():
                self.assertLess(cup.intersect(solid).Volume(), 1e-7, name)
            tray = scene['SERVICE_CS05_swivel_tray']
            support_probe = c.base.cyl_z(z - 12.6, z - 12.5, 4, 96, 406).val()
            self.assertAlmostEqual(tray.intersect(support_probe).Volume(), support_probe.Volume(), places=7)

    def test_released_swivel_has_clearance_against_suspended_cup(self):
        c = self.c
        z = c.C['center_stops_mm']['HIGH']
        cup = c.base.cyl_z(z - 12.5, z + 12.5, 6.1, 96, 406).val()
        for angle in range(0, 91, 15):
            scene = c.installed(z - c.C['release_drop_mm'], angle, False)
            self.assertEqual(overlap_pairs(scene), [], angle)
            for name, solid in scene.items():
                self.assertLess(cup.intersect(solid).Volume(), 1e-7, (angle, name))
            self.assertEqual(len(scene), sum(p['quantity'] for p in c.S['parts'].values()))

    def test_stowed_tray_clears_entire_counterweight_motion_cylinder(self):
        c = self.c
        # LOW cup centers cover approximately 130..190; HIGH adds the lower118 stop.
        swept_cup = c.base.cyl_z(105, 203, 6.1, 96, 406).val()
        scene = c.installed(c.C['center_stops_mm']['HIGH'] - 3, 90, False)
        for name, solid in scene.items():
            self.assertLess(swept_cup.intersect(solid).Volume(), 1e-7, name)

    def test_real_base_holes_admit_screws_and_nuts_clear_base(self):
        c = self.c
        board = c.indexed_base_board(c.base.base_board())
        scene = c.installed()
        for name, shape in scene.items():
            self.assertLess(board.intersect(shape).Volume(), 1e-7, name)
        for x, y in c.C['base_holes_xy_mm']:
            gauge = c.base.cyl_z(0, 12, 1.6, x, y).val()
            self.assertLess(board.intersect(gauge).Volume(), 1e-7)
        self.assertGreater(c.interface_checks()['base_bolt_projection_mm'], 1.0)

    def test_release_and_index_are_within_retained_travel(self):
        checks = self.c.interface_checks()
        self.assertGreater(checks['lower_release_to_endstop_margin_mm'], 6)
        self.assertGreaterEqual(checks['nominal_ring_release_clearance_mm'], 1)
        self.assertGreaterEqual(checks['admitted_cup_radial_clearance_mm'], .25)
        self.assertFalse(checks['full_cycle_qualified'])
        with self.assertRaises(ValueError):
            self.c.installed(130, 0, True)
        with self.assertRaises(ValueError):
            self.c.installed(80, 0, False)

    def test_index_holes_and_native_screw_axes_align_at_both_stops(self):
        c = self.c
        for z in c.C['center_stops_mm'].values():
            scene = c.installed(z)
            gauge = c.base.cyl_y(c.C['index_pin_underhead_y_mm'], c.C['index_nut_back_y_mm'], 1.6, 116, z).val()
            for name in ('SERVICE_CS02_indexed_rail', 'SERVICE_CS03_indexed_carriage', 'SERVICE_CS01_upright'):
                self.assertLess(scene[name].intersect(gauge).Volume(), 1e-7, (z, name))
            pin = scene['SERVICE_HW_M3x30_vertical_index'].BoundingBox()
            self.assertAlmostEqual(pin.ymax, c.C['index_pin_underhead_y_mm'] + c.C['index_screw_length_mm'], places=6)
            nut = scene['SERVICE_HW_M3nut_vertical_index'].BoundingBox()
            self.assertGreater(pin.ymax - nut.ymax, 1)


class ServiceNipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = service
        cls.ps = service.nip_parts()

    def test_nip_variants_are_single_valid_solids_and_all_instances_mapped(self):
        for name, part in self.ps.items():
            self.assertTrue(part.val().isValid(), name)
            self.assertEqual(len(part.solids().vals()), 1, name)
        counts = Counter(r['part_id'] for r in self.c.nip_inventory())
        self.assertEqual(counts, {k: v['quantity'] for k, v in self.c.S['nip_parts'].items()})

    def test_all_three_custody_states_have_no_native_overlap(self):
        for a, b in [('CLOSED', 'OPEN'), ('CLOSED', 'CLOSED'), ('OPEN', 'CLOSED')]:
            self.assertEqual(overlap_pairs(self.c.nips_installed(a, b)), [], (a, b))
        with self.assertRaises(ValueError):
            self.c.nips_installed('OPEN', 'OPEN')

    def test_closed_and_open_gaps_are_real_metal_faces_with_finished_bounds(self):
        c = self.c
        for state, expected in [('CLOSED', .5), ('OPEN', 1.5)]:
            items = c.nips_installed(state, 'CLOSED')
            upper = items['NIP_NS07_upper_pad_IN'].BoundingBox()
            lower = items['NIP_NS06_lower_pad_IN'].BoundingBox()
            self.assertAlmostEqual(upper.zmin - lower.zmax, expected, places=8)
            bounds = c.nip_gap_bounds(state)
            self.assertAlmostEqual(bounds[0], c.S['service_nips']['finish_admission'][state.lower() + '_gap_bounds_mm'][0])
            self.assertAlmostEqual(bounds[1], c.S['service_nips']['finish_admission'][state.lower() + '_gap_bounds_mm'][1])

    def test_opening_changes_upper_parts_and_shims_without_losing_retention(self):
        c = self.c
        closed = c.nips_installed('CLOSED', 'CLOSED')
        opened = c.nips_installed('OPEN', 'CLOSED')
        for name in ('NIP_NS05_upper_IN', 'NIP_NS07_upper_pad_IN', 'NIP_HW_M2x8_upper_pad_IN', 'NIP_HW_M2nut_upper_pad_IN'):
            self.assertAlmostEqual(opened[name].Center().z - closed[name].Center().z, 1, places=8)
        for i in range(2):
            name = f'NIP_HW_M2x16_actuator_{i}_IN'
            self.assertLess(opened[name].cut(closed[name]).Volume(), 1e-7)
            bolt = opened[name].BoundingBox()
            nut = opened[f'NIP_HW_M2nut_actuator_{i}_IN'].BoundingBox()
            self.assertAlmostEqual(nut.zmin - bolt.zmin, 1.9, places=8)
            self.assertGreater(nut.zmin - (bolt.zmin + 1.2), .6)
            name = f'NIP_NS09_open_shim_{i}_IN'
            self.assertAlmostEqual(closed[name].Center().z - opened[name].Center().z, 4, places=8)

    def test_yarn_lane_clears_retainer_heads_shims_and_shoulders(self):
        c = self.c
        for state in ('CLOSED', 'OPEN'):
            items = c.nips_installed(state, 'CLOSED')
            z = 238.75 + (0 if state == 'CLOSED' else .5)
            # A thin lane witness avoids declaring compression mechanics from a rigid 0.6 mm cylinder.
            witness = c.base.cyl_x(9, 23, .2, 406, z).val()
            for name, solid in items.items():
                if name.endswith('_OUT') or 'tower' in name or 'bracket' in name or 'outlet' in name:
                    continue
                self.assertLess(witness.intersect(solid).Volume(), 1e-7, (state, name))

    def test_native_key_pockets_retain_positive_walls(self):
        c = self.c
        n = c.S['service_nips']
        for x, z in n['upstream_key_xz_mm']:
            gauge = c.base.box(x - .99, x + .99, 416.01, 417.99, z - .99, z + .99).val()
            self.assertAlmostEqual(self.ps['NS03_inlet_lower'].val().intersect(gauge).Volume(), gauge.Volume(), places=7)
            self.assertLess(self.ps['NS02_tower_keyed'].val().intersect(gauge).Volume(), 1e-7)
        for x, z in n['downstream_key_xz_mm']:
            gauge = c.base.box(x - .99, x + .99, 414.01, 415.99, z - .99, z + .99).val()
            self.assertAlmostEqual(self.ps['NS01_fairlead_bracket_extended'].val().intersect(gauge).Volume(), gauge.Volume(), places=7)
            self.assertLess(self.ps['NS04_outlet_lower'].val().intersect(gauge).Volume(), 1e-7)

    def test_nip_control_transition_retains_hardware_and_clears_all_solids(self):
        c = self.c
        phases = c.S['service_nips']['opening_phases']
        initial = c.nips_installed('CLOSED', 'CLOSED')
        for active in ('IN', 'OUT'):
            for phase in phases:
                for fraction in (0., .5, 1.):
                    scene = c.nip_opening_transition(active, phase, fraction)
                    self.assertEqual(set(scene), set(initial))
                    self.assertEqual(overlap_pairs(scene), [], (active, phase, fraction))
            endpoint = c.nip_opening_transition(active, phases[-1], 1)
            expected = c.nips_installed('OPEN' if active == 'IN' else 'CLOSED',
                                        'OPEN' if active == 'OUT' else 'CLOSED')
            for name in endpoint:
                self.assertLess(endpoint[name].cut(expected[name]).Volume() + expected[name].cut(endpoint[name]).Volume(), 1e-7, name)


    def test_interface_exposes_real_open_corridor_and_closed_compression_need(self):
        for label, expected_midpoint in [('IN', 239.25), ('OUT', 238.5)]:
            opened = self.c.nip_interface(label, 'OPEN')
            closed = self.c.nip_interface(label, 'CLOSED')
            self.assertAlmostEqual(opened['gap_midpoint_xyz_mm'][2], expected_midpoint)
            self.assertFalse(opened['compression_law_required'])
            self.assertTrue(closed['compression_law_required'])
            self.assertIsNone(closed['uncompressed_center_z_interval_mm'])
            parts = self.c.nips_installed('OPEN' if label == 'IN' else 'CLOSED',
                                          'OPEN' if label == 'OUT' else 'CLOSED')
            self.assertAlmostEqual(parts[f'NIP_NS07_upper_pad_{label}'].BoundingBox().zmin,
                                   opened['upper_pad_face_z_mm'])
            self.assertAlmostEqual(parts[f'NIP_NS06_lower_pad_{label}'].BoundingBox().zmax,
                                   opened['lower_pad_face_z_mm'])


if __name__ == '__main__':
    unittest.main()
