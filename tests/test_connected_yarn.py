import unittest,numpy as np
from physics.connected_yarn import connected_objective
from physics.loop_holding import bar_direction
class Empty:
 def components(self,p):return [(np.full(len(p),1e4),np.zeros_like(p))]
class ConnectedEnergy(unittest.TestCase):
 def test_full_gradient_including_shared_clamp_node(self):
  cfg={'active_attachment_offsets_x_mm':[-22,-6],'EA_N':2.,'B_Nmm2':.02,'yarn_linear_density_g_per_m':.1786,'yarn_radius_mm':.1,'penalty_N_per_mm2':1000.,'contact_samples_per_edge':2,'neighbor_support_x_mm':[106,118,154,166,178,190],'clamp_initial_center_xyz_mm':[150,165,40],'support_contact_yz_mm':[165,90.55],'clamp_mass_g':20.}
  c=np.array([150.,165.,39.]);a=np.array([.2,.1]);q=np.array([[128,165,39],[126,166,55],[130,164,65],[142,165,54],[144,165,39],[151,167,43],[155,167,58],[160,169,64]],float);split=4;guide=q[-1].copy();q[[0,split]]=c+np.array([-22,-6])[:,None]*bar_direction(a)[0];rest=np.linalg.norm(np.diff(q,axis=0),axis=1)*.99;free=[1,2,3,5,6]
  def f(q,c,a):return connected_objective(q,rest,split,c,a,guide,cfg,Empty())
  E,g,cg,ag,info=f(q,c,a)
  for k in free:
   for j in range(3):
    p=q.copy();m=q.copy();p[k,j]+=1e-5;m[k,j]-=1e-5
    self.assertAlmostEqual((f(p,c,a)[0]-f(m,c,a)[0])/2e-5,g[k,j],places=7)
  for j in range(3):
   p=c.copy();m=c.copy();p[j]+=1e-5;m[j]-=1e-5
   self.assertAlmostEqual((f(q,p,a)[0]-f(q,m,a)[0])/2e-5,cg[j],places=7)
  for j in range(2):
   p=a.copy();m=a.copy();p[j]+=1e-5;m[j]-=1e-5
   self.assertAlmostEqual((f(q,c,p)[0]-f(q,c,m)[0])/2e-5,ag[j],places=7)
if __name__=='__main__':unittest.main()
