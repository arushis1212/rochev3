"""Native D26/T17 fit and stop checks, not fabrication qualification or a solver."""
import json
import math
from pathlib import Path
import tempfile
import unittest

from spec.effective import load_fixture
from cad.r5m2 import build as base
from cad.transfer import build as transfer


class SharedFinishedAuthority(unittest.TestCase):
    def test_relational_passages_follow_gate_and_do_not_modify_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'spec').mkdir()
            raw=json.loads((base.ROOT/'spec/r5_m2_fixture.json').read_text())
            raw['tool']['gate_thickness'] += .02
            raw_bytes=json.dumps(raw)
            (root/'spec/r5_m2_fixture.json').write_text(raw_bytes)
            (root/'spec/d26_finished_interfaces.json').write_bytes((base.ROOT/'spec/d26_finished_interfaces.json').read_bytes())
            actual=load_fixture(root)
            self.assertAlmostEqual(actual['tool']['barrel_slot_top']-raw['tool']['gate_bottom']-raw['tool']['gate_thickness'],.075)
            self.assertEqual(actual['cloth_clamp'],raw['cloth_clamp'])
            self.assertEqual(actual['feeder'],raw['feeder'])
            self.assertEqual((root/'spec/r5_m2_fixture.json').read_text(),raw_bytes)


class FinishedNativeFits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transfer=transfer.parts()
        cls.barrel=base.barrel().val()
        cls.holder=base.support_holder().val()
        cls.bed=base.support_bed().val()
        cls.cap=base.support_cap().val()
        cls.carriage=base.support_carriage().val()
        cls.bearing=base.bearing().val()
        cls.I=json.loads((base.ROOT/'spec/transfer_interfaces.json').read_text())

    def assertFits(self,host,gauge):
        self.assertLess(host.intersect(gauge).Volume(),1e-7)

    def test_passages_admit_finished_width_and_top_gauges(self):
        # The upper strip gauge extends above the old3.3628 slot top.
        top=base.T['gate_bottom']+base.T['gate_thickness']
        for host,off in [(self.barrel,0),*( (self.holder,s*base.S['support_bank']['pair_centers']/2) for s in (-1,1))]:
            gauge=base.box(-45,-40,top,top+.065,off-.87,off+.87).val()
            self.assertFits(host,gauge)
            # A gauge wider than the selected slot must contact its walls.
            oversize=base.box(-45,-40,top,top+.065,off-.885,off+.885).val()
            self.assertGreater(host.intersect(oversize).Volume(),1e-5)

    def test_barrel_bearing_and_collar_axial_admission(self):
        t=base.T
        gauge=base.cyl_x(t['bearing_back'],t['bearing_front'],16.09/2).val()
        self.assertFits(self.bearing,gauge)
        self.assertGreater(self.bearing.intersect(base.cyl_x(t['bearing_back'],t['bearing_front'],16.13/2).val()).Volume(),1e-5)
        rear=base.collar(t['bearing_back']-t['collar_axial_gap']-t['collar_thickness']).val()
        front=base.collar(t['bearing_front']+t['collar_axial_gap']).val()
        self.assertAlmostEqual(rear.distance(self.bearing),.075,places=7)
        self.assertAlmostEqual(front.distance(self.bearing),.075,places=7)
        self.assertFits(self.bearing,self.barrel)

    def test_support_and_active_stops_admit_travel_and_reject_overtravel(self):
        sleeve=base.stop_sleeve().val();pair=base.S['support_bank']['pair_centers']/2
        cases=[(self.barrel,sleeve,9.),(self.holder,sleeve.translate((0,0,-pair)),9.),(self.holder,sleeve.translate((0,0,pair)),9.),(self.transfer['TH_H03_barrel_stop'].val(),self.transfer['TH_H08_stop_sleeve'].val(),16.5)]
        for host,moving,travel in cases:
            for q in (0,travel/2,travel):self.assertFits(host,moving.translate((-q,0,0)))
            for q in (-.01,travel+.01):self.assertGreater(host.intersect(moving.translate((-q,0,0))).Volume(),1e-7)

    def test_index_pin_and_all_three_common_axis_bores(self):
        b=base.S['support_bank'];x=b['first_station_x'];y=b['bank_origin'][1]+b['index_arm_u'];z=b['bank_origin'][2]
        gauge=base.cyl_z(z-1,z+b['bank_carriage_top']+b['index_arm_height']+1,3.04/2,x,y).val()
        carriage=base.place(base.support_carriage(),(x,b['bank_origin'][1],z),(0,1,0),(0,0,1))
        for host in (self.bed,self.cap,carriage):self.assertFits(host,gauge)
        pin=base.index_pin().val();head=base.FINISH['index_pin']
        expected=math.pi*(head['shaft_d_mm']/2)**2*30+math.pi*(head['head_d_mm']/2)**2*3
        self.assertAlmostEqual(pin.Volume(),expected,places=7)
        items=base.add_bank_hardware({})
        self.assertEqual(len([n for n in items if n.startswith('B09_index_pin_')]),4)
        self.assertFalse(any(n.startswith('HW_M3x30_index_') for n in items))

    def test_cover_and_barrel_nuts_have_improved_projection(self):
        items=base.add_bank_hardware({});hook=base.add_hook_hardware({})
        for n,screw in items.items():
            if n.startswith('HW_M2x16_cover_'):
                nut=items[n.replace('HW_M2x16','HW_M2nut')]
                self.assertAlmostEqual(nut.BoundingBox().zmin-screw.BoundingBox().zmin,1.4,places=7)
                self.assertFits(self.bed,nut)
        for i in range(len(base.T['body_fix_holes_u'])):
            self.assertAlmostEqual(hook[f'HW_M2nut_body_{i}'].BoundingBox().zmin-hook[f'HW_M2x12_body_{i}'].BoundingBox().zmin,1.2,places=7)
            self.assertFits(self.barrel,hook[f'HW_M2nut_body_{i}'])

    def test_closed_nut_pockets_admit_height_and_af_gauges(self):
        # Gauges occupy the additional insertion height, so exact-height pockets fail.
        i=self.I;c=transfer.C;nh=base.S['fasteners']['M2']['nut_height_max'];h=1.79;af=4.19
        pu=sum(i['pin_shuttle_u_mm'])/2
        for sign in (-1,1):
            w=sign*c['lift_pin_w_mm']
            self.assertFits(self.transfer['R19_pin_shuttle'].val(),base.hex_y(nh-h,nh,af,pu,w).val())
            a=c['stripper_channel_mm']/2+c['stripper_plate_thickness_mm']+c['lift_carriage_plate_gap_mm']
            rod_u=a+c['lift_pin_embed_mm']/2+c['lift_guide_u_offset_mm'];outer=c['lift_guide_w_mm']+3+nh
            lo,hi=sorted((sign*(outer-h),sign*outer))
            self.assertFits(self.transfer['R06_anchor'].val(),base.hex_z(lo,hi,af,rod_u,i['guide_screw_v_mm']).val())
        face=i['reset_nut_face_u_mm'];v=i['reset_stop_axis_v_mm']
        gauge=base.place(base.hex_z(0,h,af),(face,v,0),(0,0,1),(-1,0,0))
        self.assertFits(self.transfer['R05_lift_carriage'].val(),gauge)
        nut=self.transfer['R24_reset_nut'].val();screw=self.transfer['R23_reset_screw'].val()
        self.assertAlmostEqual(nut.BoundingBox().xmin-screw.BoundingBox().xmin,1.1,places=7)
        for host,u,roof in [(self.bearing,(base.T['bearing_back']+base.T['bearing_front'])/2,base.T['roll_lock_nut_v'][1]),(base.guide_mount().val(),base.S['guide']['mount_back_u']+base.S['guide']['mount_block'][0]/2,base.S['guide']['outer_lock_nut_v'][1])]:
            self.assertFits(host,base.hex_y(roof-2.69,roof,5.79,u).val())

    def test_reach_mount_holes_follow_new_stage_origin(self):
        board=base.base_board().val();origin=base.S['frame']['head_x_origin']
        for x in (98,114):self.assertFits(board,base.cyl_z(-1,13,3.39/2,x,60).val())
        center=origin[0]+base.S['frame']['tool_lateral_offset']
        self.assertAlmostEqual(center,148.)
        for target in (95.5,200.5):self.assertLessEqual(abs(target-center),60.)

    def test_changed_parts_remain_single_valid_solids(self):
        for name,p in self.transfer.items():
            self.assertTrue(p.val().isValid(),name)
            self.assertEqual(len(p.solids().vals()),1,name)
        for shape in (self.barrel,self.holder,self.bed,self.cap,self.carriage,self.bearing,base.index_pin().val()):
            self.assertTrue(shape.isValid())
            self.assertEqual(len(shape.Solids()),1)


if __name__=='__main__':unittest.main()
