import unittest
import numpy as np
from physics.roche_contact3d import self_contact,self_pairs,closest_segments

def exhaustive(q,rest,r,k,pairs):
    i,j=pairs;g=np.zeros_like(q)
    if not len(i):return 0.,g,float('inf')
    d,delta,s,t=closest_segments(q[i],q[i+1],q[j],q[j+1]);depth=np.maximum(2*r-d,0)
    weight=rest[i]*rest[j]/(2*r);force=(-k*weight*depth)[:,None]*delta/np.maximum(d[:,None],1e-14)
    np.add.at(g,i,(1-s)[:,None]*force);np.add.at(g,i+1,s[:,None]*force)
    np.add.at(g,j,-(1-t)[:,None]*force);np.add.at(g,j+1,-t[:,None]*force)
    return float(.5*k*np.dot(weight,depth*depth)),g,float(np.min(d)-2*r)

class ExactCulling(unittest.TestCase):
    def compare(self,q,r):
        rest=np.linalg.norm(np.diff(q,axis=0),axis=1);pairs=self_pairs(rest,r)
        actual=self_contact(q,rest,r,17.,pairs);expected=exhaustive(q,rest,r,17.,pairs)
        for a,b in zip(actual,expected):np.testing.assert_allclose(a,b,atol=1e-10,rtol=1e-12)
    def test_random_and_sparse_strands_match_exhaustive_oracle(self):
        rng=np.random.default_rng(835)
        for scale in [.02,.3,2.,10.]:
            for n in [8,30,129]:self.compare(np.cumsum(rng.normal(0,scale,(n,3)),axis=0),.3)
        t=np.linspace(0,100,257);self.compare(np.column_stack([t,np.sin(t/10),np.cos(t/10)]),.3)
    def test_parallel_crossing_and_near_threshold(self):
        for z in [.5999999999,.6,.6000000001,10.]:
            self.compare(np.array([[0.,0,0],[2,0,0],[3,3,0],[1,3,z],[1,-2,z]]),.3)
