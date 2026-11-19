"""Physical coverage and material-specific ideal-grip reduction regressions."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import cadquery as cq
import numpy as np

from physics.fixture_contact import ClampContact,clamp_pad_boxes
from physics.collision_aware_steps import adaptive_solid_bound
from physics.roche_contact3d import contact_energy3d
from physics.feed_native import upstream_clearance


ROOT=Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT/'spec/r5_m2_fixture.json').read_text())['cloth_clamp']


def gripping():
    q=np.array([[-7.95,0.,z]for z in [2.65,3.35,4.65,5.35]])
    return q,{'indices':[0,1,2,3],'body_xyz_mm':q.tolist(),'gripped_edges':[0,1,2]}


def box(lo,hi):
    return cq.Workplane('XY').box(*(np.asarray(hi)-lo)).translate(tuple((np.asarray(hi)+lo)/2)).val()


class GripContactTests(unittest.TestCase):
    def setUp(self):
        self.q,self.section=gripping()
        self.clamp=ClampContact(fixture(),[0,0,0],[0,0,0],self.section)

    def test_only_registered_material_gets_own_pad_reduction(self):
        points=np.array([[-7.95,0,4.],[-22.,.5,4.]])
        plain=self.clamp.distance(points)[0]
        reduced=self.clamp.distance_for_edges(points,[1,1])[0]
        self.assertLess(plain[0],.3)
        self.assertGreater(reduced[0],.3)
        self.assertAlmostEqual(plain[1],reduced[1])
        np.testing.assert_allclose(self.clamp.distance_for_edges(points,[99,99])[0],plain)

    def test_pin_jaws_spacers_and_bolts_are_never_excluded(self):
        points=np.array([[-6,0,1.],[-7.95,-1.5,4.],[-12,0,2.8],[0,0,0.]])
        plain=self.clamp.distance(points)[0]
        reduced=self.clamp.distance_for_edges(points,np.ones(len(points),dtype=int))[0]
        self.assertTrue(np.all(reduced<0))
        np.testing.assert_allclose(reduced,plain)

    def test_registration_rejects_free_edges_and_unlocated_grips(self):
        missing=copy.deepcopy(self.section);missing['indices']=missing['indices'][:-1];missing['body_xyz_mm']=missing['body_xyz_mm'][:-1]
        with self.assertRaisesRegex(ValueError,'two prescribed'):self.clamp.set_gripped_edges(missing)
        outside=copy.deepcopy(self.section);outside['body_xyz_mm'][1][2]=0
        with self.assertRaisesRegex(ValueError,'physical grip'):self.clamp.set_gripped_edges(outside)
        duplicate=copy.deepcopy(self.section);duplicate['gripped_edges']=[1,1]
        with self.assertRaisesRegex(ValueError,'unique'):self.clamp.set_gripped_edges(duplicate)

    def test_material_specific_contact_energy_and_spatial_bound_agree(self):
        rest=np.linalg.norm(np.diff(self.q,axis=0),axis=1)
        raw=ClampContact(fixture(),[0,0,0],[0,0,0])
        self.assertGreater(contact_energy3d(self.q,rest,.3,1000.,raw,8)[0],0)
        self.assertAlmostEqual(contact_energy3d(self.q,rest,.3,1000.,self.clamp,8)[0],0)
        self.assertGreaterEqual(adaptive_solid_bound(self.q,self.clamp)['lower']-.3,-.01)
        self.assertLess(adaptive_solid_bound(self.q,raw)['lower']-.3,-.01)

    def test_reduced_obstacle_stays_lipschitz_across_region_boundary(self):
        rng=np.random.default_rng(28)
        points=np.array([-7.95,.3,3.])+rng.uniform(-.7,.7,(200,3))
        moves=rng.normal(size=(200,3))*.03
        a=self.clamp.distance_for_edges(points,np.ones(200,dtype=int))[0]
        b=self.clamp.distance_for_edges(points+moves,np.ones(200,dtype=int))[0]
        self.assertTrue(np.all(abs(a-b)<=np.linalg.norm(moves,axis=1)+1e-12))

    def test_body_pose_and_gradient_transform_consistently(self):
        local=np.array([[-7.7,.4,4.]])
        d,g=self.clamp.distance_for_edges(local,[1])
        self.clamp.set_pose([3.,-2.,5.],[4.,7.,-3.])
        world=self.clamp.center+local@self.clamp.R.T
        moved,gradient=self.clamp.distance_for_edges(world,[1])
        np.testing.assert_allclose(moved,d,atol=1e-12)
        np.testing.assert_allclose(gradient,g@self.clamp.R.T,atol=1e-12)

    def test_native_rounded_pad_is_contained_by_contact_cover(self):
        spec=fixture();g=spec['closed_face_gap_mm']/2;p=g+spec['pad_thickness_mm']
        native=box([-44,-p,-5],[44,-g,5])
        window=cq.Workplane('XZ').center(-6,0).rect(6,6).extrude(3,both=True).edges('|Y').fillet(.5).val()
        native=native.cut(window)
        pieces=[box(lo,hi)for lo,hi in clamp_pad_boxes(spec)]
        cover=pieces[0].fuse(*pieces[1:])
        self.assertLess(native.cut(cover).Volume(),1e-8)
        self.assertGreater(self.clamp.pads.distance(np.array([[-6.,-.5,0.]]))[0][0],1.)
        self.assertLess(self.clamp.pads.distance(np.array([[-8.9,-.5,-2.9]]))[0][0],0.)

    def test_clipped_dispatch_preserves_material_edge_ids_after_subdivision(self):
        clamp=self.clamp
        class Forwarded:
            def __init__(self):self.seen=[]
            def distance_for_edges(self,p,edge_ids):return clamp.distance_for_edges(p,edge_ids)
            def clipped_distance(self,p,ceiling,edge_ids=None):
                self.seen.extend(edge_ids.tolist())
                return np.minimum(self.distance_for_edges(p,edge_ids)[0],ceiling)
        obstacle=Forwarded()
        result=adaptive_solid_bound(self.q,obstacle)
        self.assertGreaterEqual(result['lower']-.3,-.01)
        self.assertEqual(set(obstacle.seen),{0,1,2})

    def test_legacy_clipped_distance_signature_still_works(self):
        class Legacy:
            def clipped_distance(self,p,ceiling):return np.asarray(ceiling)
        self.assertGreater(adaptive_solid_bound(self.q,Legacy())['lower'],0)

    def native_scene(self):
        window=cq.Workplane('XZ').center(-6,0).rect(6,6).extrude(3,both=True).edges('|Y').fillet(.5).val()
        return {'D02_pad_A':box([-44,-1.25,-5],[44,-.25,5]).cut(window),
                'D02_pad_B':box([-44,.25,-5],[44,1.25,5]).cut(window)}

    def test_native_reduction_is_bounded_and_reported(self):
        scene=self.native_scene()
        with patch('physics.feed_native.hardware',return_value=({},{})),patch('physics.feed_native.install.installed',return_value=scene):
            plain=upstream_clearance(self.q,[0,0,0,0],[0,0,0],clamp_pose=([0,0,0],[0,0,0]))
            reduced=upstream_clearance(self.q,[0,0,0,0],[0,0,0],clamp_pose=([0,0,0],[0,0,0]),fixed_section=self.section)
        self.assertTrue(plain['violations'])
        self.assertFalse(reduced['violations'])
        self.assertEqual(reduced['grip_exclusions']['gripped_edges'],[0,1,2])
        self.assertFalse(reduced['grip_exclusions']['qualified_retention'])
        self.assertEqual({x['part']for x in reduced['grip_exclusions']['applied_native_reductions']},{'D02_pad_A','D02_pad_B'})

    def test_native_pin_collision_survives_own_pad_reduction(self):
        scene=self.native_scene();scene['D03_return_pin']=box([-8.1,-.1,3.7],[-7.8,.1,4.3])
        with patch('physics.feed_native.hardware',return_value=({},{})),patch('physics.feed_native.install.installed',return_value=scene):
            result=upstream_clearance(self.q,[0,0,0,0],[0,0,0],clamp_pose=([0,0,0],[0,0,0]),fixed_section=self.section)
        self.assertIn('D03_return_pin',{x['part']for x in result['violations']})


if __name__=='__main__':unittest.main()
