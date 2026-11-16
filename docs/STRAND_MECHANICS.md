# Three-dimensional contact toolkit

The current toolkit adds three-dimensional rod deformation and contact against
profiles extracted from the exact hook/closure CAD. Every interior node has
three translational degrees of freedom. Segment-to-segment proximity supplies
nonlocal strand contact forces. These are mechanics building blocks for studying
loop transfer; full connected stitch trajectories are a separate qualification.

The material examples use declared benchmark EA, bending rigidity and radius.
The code does not substitute those constants for measured yarn properties.
Friction and twist are outside this implementation's constitutive model.

Hook faces consist of lines and circular arcs. Circular boundaries are exported
with a0.001mm chord-error bound. Distance and gradient tests include independent
OpenCascade boundary queries, analytic solids, holes and finite differences.

Nonlocal contact excludes edge pairs within one semicircle of reference material;
the local tube condition radius*curvature<1 must also be checked. This prevents
mesh refinement from creating artificial contact between neighboring material.
The Newton solver uses exact local sparsity only while all nonlocal contact terms
remain inactive through the finite-difference perturbation; otherwise it uses the
full Hessian. Acceptance depends on residual force, not energy stagnation.

Rebuild the contact profiles with:

```sh
.venv/bin/python cad/r5m2/export_contact.py
```

The planar benchmark has converged through129 nodes at a1e-7N free-node residual
threshold. Its evidence applies to that prescribed-end, local pocket experiment.
The three-dimensional tools expose additional geometry and contact behavior;
their existence does not certify a whole machine or a physical crochet cycle.
