import unittest,json
from pathlib import Path
import numpy as np
from physics.rigid_clamp import rotation,migrate_line_clamp
from physics.loop_holding import bar_direction
from physics.rigid_clamp_feed import RigidClampFeedEquilibrium
from physics.feeder_domain import FeederContact
class Empty:
 def edge_contact_terms(self,*args):return iter(())
 def distance(self,p):return np.full(len(p),1e6),np.zeros_like(p)
class RigidClampTests(unittest.TestCase):
 def test_rotation_preserves_lengths_and_has_correct_derivatives(self):
  a=np.array([10.,-12.,17.]);R,d=rotation(a);np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-14);self.assertAlmostEqual(np.linalg.det(R),1.)
  for j in range(3):
   e=np.eye(3)[j]*1e-5;fd=(rotation(a+e)[0]-rotation(a-e)[0])/2e-5;np.testing.assert_allclose(d[j],fd,atol=2e-11)
 def test_migration_preserves_both_material_boundaries(self):
  c=np.array([148.9,162.3,39.86]);a=np.array([3.69,-.46]);new,b=migrate_line_clamp(c,a);R,_=rotation(b)
  for off in [-22.,-6.]:np.testing.assert_allclose(new+R@[off,0.,5.],c+off*bar_direction(a)[0],atol=1e-12)
 def test_roll_gravity_has_pendulum_restoring_curvature(self):
  # Hold grip line fixed. A COM5mm below it has U=-mgh*cos(roll).
  m=.196133;h=5.;phi=.17;scale=44.;angles=np.array([0.,0.,phi*scale]);R,d=rotation(angles);com=-R@[0,0,h]
  self.assertAlmostEqual(m*com[2],-m*h*np.cos(phi),places=12)
  self.assertAlmostEqual(-m*(d[2]@[0,0,h])[2]*scale,m*h*np.sin(phi),places=12)
 def test_full_virtual_work_including_moving_contact(self):
  root=Path(__file__).resolve().parents[1];cfg=json.loads((root/'spec/transfer_holding.json').read_text());cfg.update(contact_reference_spacing_mm=.5,yarn_linear_density_g_per_m=.1786);fixture=json.loads((root/'spec/r5_m2_fixture.json').read_text())
  q=np.array([[26.,400,175],[34,399.5,174.8],[42,400,175],[48,406,151.9],[55,406,156],[64,406,238.8]]);rest=np.linalg.norm(np.diff(q,axis=0),axis=1)*.99
  model=RigidClampFeedEquilibrium(q,rest,2,[48,400,170],[.2,-.1,.05],160,cfg,FeederContact(Empty(),160),fixture['feeder'],'LOW',fixture);x=model.x0;E,g=model.energy(x);fd=[];h=1e-5
  for j in range(len(x)):
   a=x.copy();b=x.copy();a[j]+=h;b[j]-=h;fd.append((model.energy(a)[0]-model.energy(b)[0])/(2*h))
  np.testing.assert_allclose(g,fd,rtol=3e-5,atol=3e-5)
 def test_attachment_and_solid_speed_bounds(self):
  from physics.fixture_contact import ClampContact
  root=Path(__file__).resolve().parents[1];s=json.loads((root/'spec/r5_m2_fixture.json').read_text())['cloth_clamp'];clamp=ClampContact(s,[0,0,0],[0,0,0]);delta=np.array([12.,-7.,5.]);point=np.array([50.,10.7,5.]);speed=np.linalg.norm(point)*sum(abs(delta))/44
  q=np.array([rotation(t*delta)[0]@point for t in np.linspace(0,1,1001)]);self.assertLessEqual(np.linalg.norm(np.diff(q,axis=0),axis=1).max()*1000,speed)
class AdaptiveMaterialTests(unittest.TestCase):
 def test_bisection_preserves_old_vertices_and_rest_domain(self):
  from physics.material_mesh import refine_selected
  q=np.array([[0.,0,0],[1.,1,0],[2.,1,0],[3.,1,0]]);r=np.array([1.3,.9,1.2]);p,s,split,mapping=refine_selected(q,r,2,[0,2]);np.testing.assert_array_equal(p[mapping],q);np.testing.assert_allclose(np.r_[0,np.cumsum(s)][mapping],np.r_[0,np.cumsum(r)],atol=1e-14);self.assertEqual(split,3);self.assertAlmostEqual(sum(s),sum(r))
 def test_invalid_refinement_rejected(self):
  from physics.material_mesh import refine_selected
  q=np.array([[0.,0,0],[1,1,0],[2,0,0]]);r=np.ones(2)
  for choice in [[-1],[2],[True],[0,0]]:
   with self.assertRaises(ValueError):refine_selected(q,r,1,choice)
