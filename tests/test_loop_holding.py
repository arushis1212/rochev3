import unittest,json,numpy as np
from pathlib import Path
from physics.loop_holding import tension_members,bar_direction,initial_state,objective
class NoContact:
    def distance(self,p):return np.full(len(p),100.),np.zeros_like(p)
class HoldingMechanics(unittest.TestCase):
    def test_tension_members_exact_and_no_compressive_textile_force(self):
        anchors=np.zeros((2,3));points=np.array([[0,0,10.1],[0,0,9.]])
        E,g=tension_members(points,anchors,np.array([10.,10.]),2.)
        self.assertAlmostEqual(E,.001,places=12);np.testing.assert_allclose(g,[[0,0,.02],[0,0,0]],atol=1e-12)
    def test_bar_derivatives(self):
        a=np.array([4.,-3.]);n,da,db=bar_direction(a);h=1e-5
        for i,g in enumerate([da,db]):
            d=np.zeros(2);d[i]=h;np.testing.assert_allclose(g,(bar_direction(a+d)[0]-bar_direction(a-d)[0])/(2*h),atol=1e-10)
        self.assertAlmostEqual(np.linalg.norm(n),1.)
    def test_clamp_force_and_torque_chain_rule(self):
        cfg=json.loads((Path(__file__).resolve().parents[1]/'spec/loop_holding.json').read_text());q,rest,c,a=initial_state(cfg,cfg['head_tip_trials_xyz_mm'][0]);c+=np.array([.2,.1,-.8]);a+=np.array([.5,-.3])
        E,g,cg,ag,_=objective(q,rest,c,a,cfg,NoContact());h=1e-5
        for i in range(5):
            cp=c.copy();cm=c.copy();ap=a.copy();am=a.copy()
            if i<3:cp[i]+=h;cm[i]-=h;expected=cg[i]
            else:ap[i-3]+=h;am[i-3]-=h;expected=ag[i-3]
            actual=(objective(q,rest,cp,ap,cfg,NoContact())[0]-objective(q,rest,cm,am,cfg,NoContact())[0])/(2*h)
            self.assertAlmostEqual(actual,expected,places=6)
    def test_diagnostics_are_strict_json_serializable(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from physics.loop_holding import solve_holding
        cfg=json.loads((Path(__file__).resolve().parents[1]/'spec/loop_holding.json').read_text());q,rest,c,a=initial_state(cfg,cfg['head_tip_trials_xyz_mm'][0]);x=np.concatenate([q[1:-1].ravel(),c,a])
        with patch('physics.loop_holding.minimize',return_value=SimpleNamespace(x=x,nit=0,message='serialization-only fixture')):
            _,_,_,info=solve_holding(q,rest,c,a,cfg,NoContact())
        json.dumps(info,allow_nan=False);self.assertIs(type(info['optimizer_success']),bool)
    def test_holding_datums_match_current_machine(self):
        root=Path(__file__).resolve().parents[1];cfg=json.loads((root/'spec/loop_holding.json').read_text());machine=json.loads((root/'spec/r5_m2_fixture.json').read_text());bank=machine['support_bank']
        xs=[bank['first_station_x']+i*bank['station_pitch']+side*bank['pair_centers']/2 for i in range(bank['station_count']) if i!=1 for side in [-1,1]]
        self.assertEqual(xs,cfg['neighbor_support_x_mm']);self.assertEqual(cfg['clamp_mass_g'],machine['take_down']['target_total_mass_g'])
        self.assertEqual(cfg['support_contact_yz_mm'],[bank['standard_tip_y']+machine['tool']['body_tip'],bank['tool_axis_z']+.55])
