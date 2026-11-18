# Elastic component interfaces

The component library uses three displacement components per node and quadratic
tetrahedral displacement interpolation. Material inputs use millimetres, newtons
and MPa. The example assumes homogeneous, isotropic, small-strain elasticity.

At an ideal rigid interface, each selected node follows

`u_i = t + theta × (x_i − x_origin)`.

A sparse transformation `Q` maps interior displacements and the six interface
coordinates into all nodal displacements. The component solve uses
`K_reduced = Q.T @ K @ Q`. Distributed body loads and a six-component interface
wrench enter separately, preserving their actual lines of action.

Each response checks the reduced residual, global force and moment balance,
and the linear elastic energy identity `2 U = external work`. The benchmark
also checks reciprocal, positive compliance and exact rigid interface motion.

The cantilever example has length 30 mm, a 2 × 2 mm section, E=2000 MPa and
Poisson ratio 0.3. Axial displacement is compared with `F L / (E A)`;
transverse displacement with `F L^3 / (3 E I)`, where `I=4/3 mm^4`.
A distributed axial load is checked independently of an endpoint force.
These analytical comparisons use a 3% discretization/model tolerance.

Install the optional numerical dependencies and run the six benchmarks:

```sh
python -m pip install -r requirements-fea.txt
python -m unittest benchmarks.test_rigid_port -v
```

The ideal rigid interface represents a specified boundary condition. Real
bearings, bolt preload, contact separation, friction and printed-material
anisotropy require their corresponding models and measured inputs. Component
responses can be used in an assembly only with compatible loads and interfaces.
