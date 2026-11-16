import unittest,numpy as np
from physics.guide_contact import annular_cylinder
from cad.r5m2 import build as b
class GuideDistance(unittest.TestCase):
 def test_annular_distance_matches_cad_and_gradient(self):
  solid=b.cyl_x(-18,0,.79375).cut(b.cyl_x(-19,1,.43815)).val()
  points=np.array([[1,.6,.1],[-2,0,.2],[-17,.2,.6],[-8,2,1],[-18.3,.3,.3]],float)
  d,g=annular_cylinder(points,[1,0,0],[0,0,0],-18,0,.43815,.79375)
  for i,p in enumerate(points):
   expected=min(face.distance(b.cq.Vertex.makeVertex(*p)) for face in solid.Faces())*(-1 if solid.isInside(tuple(p),1e-8) else 1);self.assertAlmostEqual(d[i],expected,places=7)
   for j in range(3):
    a=points.copy();c=points.copy();a[i,j]+=1e-6;c[i,j]-=1e-6
    fd=(annular_cylinder(a,[1,0,0],[0,0,0],-18,0,.43815,.79375)[0][i]-annular_cylinder(c,[1,0,0],[0,0,0],-18,0,.43815,.79375)[0][i])/2e-6
    self.assertAlmostEqual(fd,g[i,j],places=6)
