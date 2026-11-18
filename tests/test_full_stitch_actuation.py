from copy import deepcopy
import unittest
import numpy as np

from physics.full_stitch_actuation import CaptureTranslationPath


class CaptureActuationTests(unittest.TestCase):
    def states(self):
        a = dict(head_tip_mm=[10.,20.,30.], guide_tip_mm=[50.,60.,70.], main_gate_mm=0.,
            head_inclination_deg=30., head_roll_deg=180., lift_mm=0., reset_mm=0.,
            machine_configuration={'station_index':1,'dock_height_mm':10.})
        b = deepcopy(a); b.update(head_tip_mm=[11.,22.,33.], guide_tip_mm=[54.,65.,76.],main_gate_mm=4.)
        return a,b

    def test_interpolation_preserves_other_controls_and_copies(self):
        a,b=self.states();p=CaptureTranslationPath(a,b);s=p.state_at(.25)
        np.testing.assert_allclose(s['head_tip_mm'],[10.25,20.5,30.75])
        self.assertEqual(s['main_gate_mm'],1.)
        self.assertEqual(s['machine_configuration'],a['machine_configuration'])
        s['machine_configuration']['station_index']=3
        self.assertEqual(p.state_at(0)['machine_configuration']['station_index'],1)
        a['head_tip_mm'][0]=999
        self.assertEqual(p.state_at(0)['head_tip_mm'][0],10.)

    def test_rejects_hidden_rotation_lift_and_service_changes(self):
        for key in ('head_roll_deg','lift_mm','reset_mm'):
            a,b=self.states();b[key]+=1
            with self.assertRaisesRegex(ValueError,'Only head/guide'):
                CaptureTranslationPath(a,b)
        a,b=self.states();b['machine_configuration']['dock_height_mm']=30
        with self.assertRaises(ValueError):CaptureTranslationPath(a,b)
        a,b=self.states();p=CaptureTranslationPath(a,b)
        for t in (-1,1.1,float('nan')):
            with self.assertRaises(ValueError):p.state_at(t)

    def test_stage_hierarchy_and_guide_world_signs(self):
        p=CaptureTranslationPath(*self.states())
        names=['HEAD_X_A01_x_rail','HEAD_X_A02_carriage','HEAD_Y_A01_y_rail',
            'HEAD_Y_A02_carriage','HEAD_Z_A01_z_rail','HEAD_Z_A02_carriage',
            'GUIDE_X_A02_carriage','GUIDE_Y_HW_M3nut_carriage_0','GUIDE_Z_A02_carriage',
            'HEAD_HW_M3x20_base_0','HEAD_HW_M3x12_XY_0','HEAD_F01_z_bracket',
            'GUIDE_F05_adapter','GUIDE_TOOL_G01_guide_tube']
        expected=[[0,0,0],[1,0,0],[1,0,0],[1,2,0],[1,2,0],[1,2,3],
            [4,0,0],[4,5,0],[4,5,6],[0,0,0],[1,0,0],[1,2,0],[4,5,6],[4,5,6]]
        result=p.native_translations(dict.fromkeys(names,'fixed'))
        for name,value in zip(names,expected):np.testing.assert_allclose(result[name],value)

    def test_gate_inclined_translation_includes_all_mounted_hardware(self):
        p=CaptureTranslationPath(*self.states())
        names=['TOOL_H02_gate','TOOL_H07_gate_knob','TOOL_H08_stop_sleeve',
            'TOOL_HW_M2x20_gate','TOOL_HW_M2nut_gate','TOOL_H03_barrel_stop']
        result=p.native_translations(dict.fromkeys(names,'fixed'))
        expected=np.array([1.,2.,3.])+[0.,-2*np.sqrt(3),2.]
        for name in names[:-1]:np.testing.assert_allclose(result[name],expected)
        np.testing.assert_allclose(result[names[-1]],[1,2,3])

    def test_unknown_axis_and_double_ownership_fail_closed(self):
        p=CaptureTranslationPath(*self.states())
        for inventory in ({'HEAD_X_new_motor':'fixed'}, {'GUIDE_TOOL_G01_guide_tube':'clamp'},
                {'anything':'unregistered'},{}):
            with self.assertRaises(ValueError):p.native_translations(inventory)

    def test_analytical_world_matches_moving_native_groups(self):
        p=CaptureTranslationPath(*self.states())
        names={'TOOL_H02_gate':'a_renamed_gate','GUIDE_TOOL_G06_exit_insert':'exit',
               'D01_jaw_A':'yoke','D01_jaw_B':'yoke','P05_moving_0':'pulley'}
        coverage={name:{'contact_id':component}for name,component in names.items()}
        native=p.native_translations(dict.fromkeys(names,'fixed'))
        components=dict.fromkeys(set(names.values()),None)
        result=p.analytical_translations(components,coverage,native)
        np.testing.assert_allclose(result['a_renamed_gate'],p.head_delta+p.gate_displacement)
        np.testing.assert_allclose(result['exit'],p.guide_delta)
        np.testing.assert_allclose(result['yoke'],[0,0,0])
        result['exit'][0]=999
        np.testing.assert_allclose(native['GUIDE_TOOL_G06_exit_insert'],p.guide_delta)

    def test_analytical_registry_rejects_omissions_unknowns_and_mixed_motion(self):
        p=CaptureTranslationPath(*self.states())
        parts={'TOOL_H02_gate':'gate','TOOL_H03_barrel_stop':'body'}
        coverage={name:{'contact_id':component}for name,component in parts.items()}
        native=p.native_translations(dict.fromkeys(parts,'fixed'))
        components={'gate':None,'body':None}
        bad_cases=[({**components,'new_contact':None},coverage,native),
            (components,coverage,{'TOOL_H02_gate':native['TOOL_H02_gate']}),
            ({'gate':None},coverage,native),
            ({'gate':None},{name:{'contact_id':'gate'}for name in parts},native),
            (components,{'TOOL_H02_gate':{}},native),
            (components,coverage,{**native,'TOOL_H02_gate':[np.inf,0,0]})]
        for args in bad_cases:
            with self.assertRaises(ValueError):p.analytical_translations(*args)

    def test_finite_endpoints_cannot_overflow_motion_or_combined_gate_translation(self):
        a,b=self.states();a['head_tip_mm']=[-1e308,0,0];b['head_tip_mm']=[1e308,0,0]
        with self.assertRaisesRegex(ValueError,'endpoint differences'):CaptureTranslationPath(a,b)
        a,b=self.states();a['guide_tip_mm']=[0,-1e308,0];b['guide_tip_mm']=[0,1e308,0]
        with self.assertRaises(ValueError):CaptureTranslationPath(a,b)
        a,b=self.states();a['head_tip_mm']=[0,0,0];b['head_tip_mm']=[0,-1e308,0]
        b['main_gate_mm']=1.7e308
        p=CaptureTranslationPath(a,b)
        with self.assertRaises(ValueError):p.native_translations({'TOOL_H02_gate':'fixed'})


if __name__=='__main__':unittest.main()
