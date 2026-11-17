"""Manufactured indexed interfaces and explicit manual service integration."""
import math
import json
import unittest
import numpy as np
from cad.r5m2 import build as b
from cad.transfer import build as t,indexed as i,indexed_validation as v


class IndexedTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.bp=b.parts();cls.tp=t.parts();cls.parts=i.parts()

    def scene(self,**kw):
        options=dict(station_index=1,roll=20,head_roll=90,head_tip=[200.5,150,94],gate=0,lift=6)
        options.update(kw)
        return i.installed(self.bp,self.tp,**options)

    def test_authored_parts_valid_single_solids_and_complete_metadata(self):
        self.assertEqual(set(self.parts),set(i.S['parts']))
        for name,obj in self.parts.items():
            self.assertTrue(obj.val().isValid(),name)
            self.assertEqual(len(obj.solids().vals()),1,name)
            self.assertGreater(obj.val().Volume(),0,name)
            self.assertIn('source_id',i.S['parts'][name])

    def test_actual_station_locator_bores_and_positive_blind_reserve(self):
        for x in i.detents():
            port=(x+i.S['index_port_xy_mm'][0],i.S['rail_origin_mm'][1]+i.S['index_port_xy_mm'][1])
            gauge=b.cyl_z(264,270,3.01/2,*port).val()
            self.assertLess(gauge.intersect(self.parts['XT01_crossbeam'].val()).Volume(),1e-7,x)
        tip=i.S['index_pin_seat_z_mm']-i.S['index_pin_shaft_length_mm']
        self.assertGreater(tip-i.S['index_beam_hole_bottom_mm'],0)
        self.assertEqual(i.detents(),[60,112,136,160,184])

    def test_key_pilot_and_antirotation_head_real_material(self):
        shoe=self.parts['XT06_keyed_shoe'].val()
        for w in i.S['key_w_mm']:
            gauge=b.cyl_x(*i.S['shoe_u_mm'],3.01/2,i.S['key_v_mm'],w).val()
            self.assertLess(gauge.intersect(shoe).Volume(),1e-7)
        key=self.parts['XT08_diamond_key'].val()
        self.assertGreater(key.Volume(),50)
        self.assertLess(b.box(0,5,-2,2,1.455,2).val().intersect(key).Volume(),1e-7)

    def test_symmetric_variants_keep_running_paths_and_functional_ports(self):
        c=t.C;a=c['stripper_channel_mm']/2+c['stripper_plate_thickness_mm']+c['lift_carriage_plate_gap_mm']
        u=a+c['lift_pin_embed_mm']/2+c['lift_guide_u_offset_mm']
        for w in (-c['lift_guide_w_mm'],c['lift_guide_w_mm']):
            gauge=b.cyl_y(-10,22,3.025/2,u,w).val()
            for n in ('XT10_lift_carriage','XT11_anchor'):self.assertLess(self.parts[n].val().intersect(gauge).Volume(),1e-7)
        interface=json.loads((b.ROOT/'spec/transfer_interfaces.json').read_text())
        for w in interface['frame_port_w_mm']:
            gauge=b.cyl_x(*interface['fork_u_mm'],3.3/2,interface['frame_port_v_mm'],w).val()
            self.assertLess(self.parts['XT11_anchor'].val().intersect(gauge).Volume(),1e-7)

    def test_expanded_reliefs_retain_material_around_functional_bores(self):
        c=t.C;interface=json.loads((b.ROOT/'spec/transfer_interfaces.json').read_text())
        a=c['stripper_channel_mm']/2+c['stripper_plate_thickness_mm']+c['lift_carriage_plate_gap_mm']
        u=a+c['lift_pin_embed_mm']/2+c['lift_guide_u_offset_mm']
        guide_cores=[b.cyl_y(-10,22,2,u,w).val()for w in (-c['lift_guide_w_mm'],c['lift_guide_w_mm'])]
        pin_cores=[b.cyl_x(2.7,26.1,1,c['lift_park_v_mm'],w).val()for w in (-c['lift_pin_w_mm'],c['lift_pin_w_mm'])]
        fork_cores=[b.cyl_x(*interface['fork_u_mm'],2.5,interface['frame_port_v_mm'],w).val()for w in interface['frame_port_w_mm']]
        for old,new,cores in [('R05_lift_carriage','XT10_lift_carriage',guide_cores+pin_cores),
                              ('R06_anchor','XT11_anchor',guide_cores+fork_cores)]:
            removed=self.tp[old].val().cut(self.parts[new].val())
            self.assertGreater(removed.Volume(),0)
            for core in cores:self.assertLess(removed.intersect(core).Volume(),1e-7,(new,core.Center().toTuple()))

    def test_finished_external_relief_and_local_rail_head_budget(self):
        scene=self.scene(lift=0)
        for a,c in [('TRANSFER_R05_lift_carriage','B06_knockover'),('TRANSFER_R06_anchor','B04_holder_2')]:
            self.assertGreaterEqual(scene[a].distance(scene[c]),.8-1e-7,(a,c))
        fit=i.S['manufacturing']['rail_mount_head_running_fit']
        worst=fit['floor_height_mm']-fit['floor_tolerance_mm']-fit['socket_seat_height_mm']-fit['socket_seat_tolerance_mm']-fit['M3_head_height_max_mm']
        self.assertAlmostEqual(worst,.165)
        self.assertGreater(worst,fit['required_gap_min_mm'])

    def test_selected_print_orientations_fit_real_build_envelope_with_brims(self):
        for name,metadata in i.S['parts'].items():
            if metadata['material']!='PLA':continue
            bb=self.parts[name].val().BoundingBox();x,y,z=bb.xlen,bb.ylen,bb.zlen
            axes=(z,y,x)if name=='XT02_upright'else(z,x,y)if name=='XT05_carrier'else(x,y,z)if name in ('XT03_index_rail','XT04_index_carriage')else(y,z,x)
            brim=metadata['brim_mm']
            for actual,limit in zip((axes[0]+2*brim,axes[1]+2*brim,axes[2]),metadata['printer_build_envelope_mm']):
                self.assertLessEqual(actual,limit,name)

    def test_actual_guide_park_travel_and_slide_stop_margins(self):
        self.assertEqual(b.joint_limit_violations([200.5,150,94],i.S['guide_index_park_mm']),[])
        half=(i.S['rail_length_mm']-2*b.P['endstop_thickness']-b.P['carriage_length'])/2
        self.assertGreaterEqual(min(half-abs(x-i.S['rail_origin_mm'][0])for x in i.detents()),6)
        for args in ({'x':59,'index_locked':True},{'x':60,'index_locked':False,'dock_height':0},{'x':200,'index_locked':False,'dock_height':30}):
            with self.assertRaises(ValueError):i.hardware(self.bp,roll=20,**args)

    def test_head_roll_is_independent_of_parked_transfer(self):
        a=self.scene(transfer_x=60,dock_height=30,head_roll=0,support_q=[0]*4)
        c=self.scene(transfer_x=60,dock_height=30,head_roll=150,support_q=[0]*4,support_gate_q=[0,1,0,0])
        self.assertLess(a['TRANSFER_R01_front_stripper'].cut(c['TRANSFER_R01_front_stripper']).Volume(),1e-7)
        self.assertGreater(a['TOOL_H01_hook_body'].cut(c['TOOL_H01_hook_body']).Volume(),.1)

    def test_service_rejects_unraised_lift_and_park_rekey(self):
        source=self.scene(lift=0)
        with self.assertRaises(ValueError):i.service_pose(source,136,20,20,0,30,'withdraw',1)
        with self.assertRaises(ValueError):i.service_pose(source,60,20,-20,30,30,'rekey',1)

    def test_service_final_pose_equals_real_dock_with_all_hardware(self):
        source=self.scene();target=self.scene(roll=-20,dock_height=30)
        end=i.service_pose(source,136,20,-20,0,30,'nuts_in',1)
        self.assertEqual(set(source),set(end));self.assertEqual(set(end),set(target))
        for name in end:
            np.testing.assert_allclose(end[name].Center().toTuple(),target[name].Center().toTuple(),atol=1e-7,err_msg=name)

    def test_native_critical_seated_states_include_all_added_fasteners(self):
        for options in ({'station_index':0,'roll':-20},{'station_index':3,'roll':20},{'transfer_x':60,'dock_height':30,'roll':-20,'support_q':[0]*4}):
            self.assertEqual(v.overlaps(self.scene(**options)),[],options)

    def test_continuous_guard_rejects_between_endpoint_collision(self):
        fixed=b.box(-.1,.1,-1,1,-1,1).val();moving=b.box(-2.1,-1.9,-.1,.1,-.1,.1).val()
        result=v.certify(lambda f:{'fixed':fixed,'moving':moving.translate((4*f,0,0))},{'moving'},4)
        self.assertFalse(result['certified'])
        with self.assertRaises(ValueError):v.certify(lambda f:{'fixed':fixed,'moving':moving},{'moving'},float('nan'))
        separated=b.box(-2.1,-1.9,1.2,1.4,-.1,.1).val()
        tight=v.certify(lambda f:{'fixed':fixed,'moving':separated.translate((4*f,0,0))},{'moving'},4,required_clearance=.3)
        self.assertFalse(tight['certified'])


if __name__=='__main__':unittest.main()
