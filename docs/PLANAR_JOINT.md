# Pressure and shear under a mounted bracket

A guide wheel loads its bracket at a distance from the mounting plane. A sideways force can lift one edge of the foot and twist the contact patch. The planar joint example estimates both effects on a fully seated rigid foot with uniform normal and tangential stiffness per unit area.

Take `y,z` from the contact area centroid. The caller supplies area, the central second moments of area and the required force and moment resultants. Normal pressure varies linearly across the face. Its constant and two slopes reproduce the normal load and its two first moments. The in-plane shear combines a constant translation with the field `(-z, y) × twist / (yy + zz)`. Integrating the two fields recovers all six load resultants. [Implementation](../examples/planar_joint.py)

The function below bounds a 7 mm × 11 mm rectangular foot carrying 94 N of normal load. The first moments are given in N·mm. The last three inputs ask the face to carry two in-plane forces in N and a twisting moment in N·mm.

```python
from examples.planar_joint import Footprint, JointLoad, bounds

area = 7 * 11
foot = Footprint(area, area*7**2/12, 0., area*11**2/12)
load = JointLoad(94., 13., -27., .8, 1.9, 6.)
minimum_pressure, maximum_pressure, required_friction = bounds(
    foot, load, (-3.5, 3.5), (-5.5, 5.5))
```

Where pressure stays positive, the largest ratio of tangential traction magnitude to pressure occurs at a corner of the bounding rectangle. Every interior traction is a convex combination of corner tractions, and the Coulomb cone is convex. A rectangular enclosure also gives a conservative limit for a drilled or relieved footprint when its actual central moments are supplied. A zero or negative pressure bound returns `None` for friction. A receiving test can compare measured retained clamping force and static friction under the intended load and dwell. [Equilibrium and edge-lift tests](../benchmarks/test_planar_joint.py) · [NASA Fastener Design Manual](https://ntrs.nasa.gov/citations/19900009424)
