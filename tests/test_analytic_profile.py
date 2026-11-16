import unittest,numpy as np
from physics.analytic_profile import wire_distance
class AnalyticProfile(unittest.TestCase):
    def test_circle_distance_and_normal_across_polygon_vertex_angles(self):
        for start,sweep in [(0,2*np.pi),(.7,2*np.pi),(.7,-2*np.pi)]:
            a=[2*np.cos(start),2*np.sin(start)]
            wire={'analytic_features':[{'kind':'CIRCLE','a':a,'b':a,'center':[0,0],'radius':2,'start_angle':start,'sweep':sweep}]}
            angles=np.linspace(-np.pi,np.pi,117);p=np.column_stack([np.cos(angles),np.sin(angles)])
            d,g=wire_distance(p,wire);np.testing.assert_allclose(d,-1,atol=1e-12);np.testing.assert_allclose(g,p,atol=1e-12)
            d,g=wire_distance(p*3,wire);np.testing.assert_allclose(d,1,atol=1e-12);np.testing.assert_allclose(g,p,atol=1e-12)
            d,_=wire_distance(np.array([[0.,0.],[3.,0.],[0.,3.]]),wire);np.testing.assert_allclose(d,[-2,1,1],atol=1e-12)
    def test_semicircle_and_straight_closing_edge(self):
        w={'analytic_features':[{'kind':'CIRCLE','a':[2,0],'b':[-2,0],'center':[0,0],'radius':2,'start_angle':0,'sweep':np.pi},{'kind':'LINE','a':[-2,0],'b':[2,0]}]}
        d,_=wire_distance(np.array([[0.,1.],[0,-1.],[0,3.],[3,0]]),w);np.testing.assert_allclose(d,[-1,1,1,1],atol=1e-12)
