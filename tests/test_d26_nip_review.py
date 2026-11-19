"""Independent material-identity and bounded own-pad checks for D26 inlet nip."""
import json
import unittest
from unittest.mock import patch
import numpy as np
from cad.r5m2 import build as cad
from physics.nip_grip import NipGrip
from physics.feeder_domain import FeederContact,NipPads
from physics.rigid_clamp_feed import RigidClampFeedEquilibrium
from physics.feed_native import upstream_clearance


class Empty:
    def edge_contact_terms(self,*args):return iter(())
    def distance(self,p):return np.full(len(p),1e6),np.zeros_like(p)


class NipReview(unittest.TestCase):
    def fixture(self):
        q=np.array([[26.,400,175],[34,399.5,174.8],[42,400,175],
                    [48,406,151.9],[55,406,156],[24,406,238.75],
                    [22.1,406,238.75],[20,406,238.75],[18,406,238.75],[16,406,238.75]])
        section={'indices':[6,7,8,9],'world_xyz_mm':q[6:].tolist()}
        return q,section

    def test_nip_alone_removes_all_held_nodes_from_free_dofs(self):
        q,section=self.fixture();rest=np.linalg.norm(np.diff(q,axis=0),axis=1)*.99
        cfg=json.loads((cad.ROOT/'spec/transfer_holding.json').read_text())
        cfg.update(contact_reference_spacing_mm=.5,yarn_linear_density_g_per_m=.1786)
        feeder=cad.S['feeder']
        model=RigidClampFeedEquilibrium(q.copy(),rest,2,[48,400,170],[.2,-.1,.05],160,cfg,
                    FeederContact(Empty(),160,feeder=feeder),feeder,'LOW',cad.S,nip_section=section)
        self.assertFalse(set(model.free)&set(section['indices']))
        x=model.x0.copy();x[:model.interior]+=.017
        np.testing.assert_array_equal(model.unpack(x)[0][section['indices']],section['world_xyz_mm'])
        np.testing.assert_array_equal(model.rest,rest)
        # Every free translation and all six clamp/feeder border variables are
        # checked against independent finite differences of the full objective.
        x=model.x0.copy();_,g=model.energy(x);fd=[];h=1e-5
        for j in range(len(x)):
            a=x.copy();b=x.copy();a[j]+=h;b[j]-=h
            fd.append((model.energy(a)[0]-model.energy(b)[0])/(2*h))
        np.testing.assert_allclose(g,fd,rtol=3e-5,atol=3e-5)

    def test_exit_edge_reduction_does_not_open_deep_pad(self):
        q,section=self.fixture();grip=NipGrip(cad.S['feeder'],section,len(q));pads=NipPads(cad.S['feeder']);pads.set_grip(grip)
        deep=np.array([[12.,406.,238.25]])
        self.assertLess(pads.distance_for_edges(deep,np.array([5]))[0][0],0)
        self.assertLess(pads.distance_for_edges(deep,np.array([4]))[0][0],0)
        self.assertGreater(pads.distance_for_edges(deep,np.array([6]))[0][0],.3)
        near_exit=np.array([[22.1,406.,238.75]])
        self.assertGreater(pads.distance_for_edges(near_exit,np.array([5]))[0][0],.3)
        bad={**section,'world_xyz_mm':[[20.,406.,238.75],*section['world_xyz_mm'][1:]]}
        with self.assertRaises(ValueError):NipGrip(cad.S['feeder'],bad,len(q))

    def test_fractional_or_boolean_material_identity_rejected(self):
        q,section=self.fixture()
        for ids in ([6.1,7.1,8.1,9.1],[True,7,8,9]):
            with self.assertRaises(ValueError):NipGrip(cad.S['feeder'],{**section,'indices':ids},len(q))

    def test_native_check_rejects_stale_registered_coordinates_in_tail_slice(self):
        q,section=self.fixture();tail=q[5:].copy();tail[2,2]+=.01
        # Keep this a boundary-validation test: no native geometry is needed
        # before a mismatched material registration must be rejected.
        with patch('physics.feed_native.hardware',return_value=({},{})),patch('physics.feed_native.install.installed',return_value={}):
            with self.assertRaises(ValueError):
                upstream_clearance(tail,[0,16.5,0,0],[96,190,96.5],edge_offset=5,nip_section=section)
            result=upstream_clearance(q[5:],[0,16.5,0,0],[96,190,96.5],edge_offset=5,nip_section=section)
        self.assertEqual(result['nip_grip_exclusions']['material_edge_offset'],5)
        self.assertEqual(result['nip_grip_exclusions']['applied_native_reductions'],[])


if __name__=='__main__':unittest.main()
