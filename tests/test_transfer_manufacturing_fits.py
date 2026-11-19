"""Native fit/ligament regressions; these are not physical qualification tests."""
import json
import math
import unittest

from cad.transfer.build import C, base, parts
from cad.transfer import installation


class TransferManufacturingFits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts = parts()
        cls.I = json.loads((base.ROOT / 'spec/transfer_interfaces.json').read_text())

    def test_both_pin_running_paths_admit_clearance_gauge(self):
        # A 1.04mm gauge rejects the old exact1mm bore; test the actual native
        # carriage, bridge and shuttle, independently of the parameter spelling.
        for w in (-C['lift_pin_w_mm'], C['lift_pin_w_mm']):
            gauge = base.cyl_x(2.7, 26.1, 1.04 / 2, C['lift_park_v_mm'], w).val()
            for name in ('R05_lift_carriage', 'R19_pin_shuttle'):
                self.assertLess(self.parts[name].val().intersect(gauge).Volume(), 1e-7, (name, w))
            for reset in (0, 3, 6):
                pin = self.parts['R03_lift_pin_0' if w < 0 else 'R03_lift_pin_1'].val()
                self.assertLess(self.parts['R05_lift_carriage'].val().intersect(pin.translate((reset, 0, 0))).Volume(), 1e-7)

    def test_both_guide_bores_admit_precision_rod_clearance_gauge(self):
        a = C['stripper_channel_mm']/2 + C['stripper_plate_thickness_mm'] + C['lift_carriage_plate_gap_mm']
        u = a + C['lift_pin_embed_mm']/2 + C['lift_guide_u_offset_mm']
        for w in (-C['lift_guide_w_mm'], C['lift_guide_w_mm']):
            gauge = base.cyl_y(-10, 22, 3.025 / 2, u, w).val()
            for name in ('R05_lift_carriage', 'R06_anchor'):
                self.assertLess(self.parts[name].val().intersect(gauge).Volume(), 1e-7, (name, w))

    def test_pilot_and_front_washer_admit_largest_sourced_sleeve(self):
        r = self.I['stop_fit_requirements']['source_sleeve_od_bounds_mm'][1] / 2
        washer = self.parts['R21_reset_front_washer'].val()
        a, b = self.I['reset_washer_front_u_mm']
        gauge = base.cyl_x(a, b, r, self.I['reset_stop_axis_v_mm']).val()
        self.assertLess(washer.intersect(gauge).Volume(), 1e-7)
        pilot = base.cyl_x(self.I['fork_u_mm'][0], self.I['lift_stop_sleeve_u_mm'][1], r, self.I['lift_stop_center_v_mm']).val()
        self.assertLess(self.parts['R06_anchor'].val().intersect(pilot).Volume(), 1e-7)

    def test_both_sides_of_both_plates_retain_worst_case_ligament_core(self):
        # This 0.5mm core excludes the two adverse0.05mm edge errors. The test
        # checks native material, not just nominal subtraction or bbox width.
        inner = C['stripper_lower_relief_halfwidth_mm'] + 0.05
        outer = C['lift_pin_w_mm'] - C['lift_pin_radius_mm'] - C['lift_slot_clearance_mm'] - 0.05
        self.assertGreaterEqual(outer - inner, 0.5 - 1e-10)
        for name in ('R01_front_stripper', 'R02_rear_stripper'):
            native = self.parts[name].val()
            box = native.BoundingBox()
            for sign in (-1, 1):
                w0, w1 = sorted((sign * inner, sign * outer))
                core = base.box(box.xmin, box.xmax, 0, 1, w0, w1).val()
                self.assertLess(core.cut(native).Volume(), 1e-7, (name, sign))

    def test_window_admission_includes_combined_registration_and_stock(self):
        f = C['manufacturing_fit_requirements']
        reserve = (C['stripper_lower_relief_halfwidth_mm'] - f['lower_window_halfwidth_tolerance_mm']
                   - (base.T['body_thickness'] + base.S['tolerances']['metal_thickness_mm'])/2
                   - base.S['guide']['compatibility_max_yarn_diameter']
                   - f['combined_registration_allowance_mm']
                   - f['additional_relative_deflection_allowance_mm']
                   - f['lower_window_inward_defect_max_mm'])
        self.assertGreater(reserve, 0.05)
        self.assertEqual(C['stripper_slot_halfwidth_mm'], 1.0128)
        self.assertEqual(C['gate_open_mm'], 16.5)
        self.assertEqual(C['lift_pin_radius_mm'], 0.5)

    def test_new_clamp_stop_spacers_follow_the_shared_pose(self):
        bp = base.parts()
        kwargs = dict(advance=0, gate=C['gate_open_mm'], lift=0, guide=installation.I['guide_park_xyz_mm'])
        nominal = installation.installed(bp, self.parts, **kwargs)
        origin = (150, 165, installation.I['take_down_z_mm'])
        target = (153, 160, origin[2] + 7)
        scale = base.S['cloth_clamp']['angular_scale_mm']
        moved = installation.installed(bp, self.parts, **kwargs, clamp_pose=(target, (math.pi * scale/2, 0, 0)))
        spacer_names = [name for name in nominal if name.startswith('D04_')]
        self.assertEqual(len(spacer_names), len(base.S['cloth_clamp']['bolt_x_mm']))
        for name in spacer_names:
            x, y, z = nominal[name].Center().toTuple()
            expected = (target[0] - (y-origin[1]), target[1] + (x-origin[0]), target[2] + z-origin[2])
            actual = moved[name].Center().toTuple()
            for a, b in zip(actual, expected):
                self.assertAlmostEqual(a, b, places=7, msg=name)


if __name__ == '__main__':
    unittest.main()
