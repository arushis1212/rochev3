# Roche

**Crochet through mechanical registration.**

Roche explores a different way to handle deformable materials: constrain the yarn
and loops where the next operation happens, then use repeatable tool motions.
The first application is a camera-free, manually actuated crochet research fixture
for single-stitch and swatch development.

This repository contains the current parametric design and executable mechanics
tools. The project combines crochet knowledge, mechanism design and numerical
engineering around a small, inexpensive physical prototype.

## Explore the design

- **83 component variants:** editable CadQuery geometry with individual STEP/STL exports.
- **522 base-assembly solids:** tooling, positioning stages, support bank, feeder,
  fasteners, stand and fabric take-down.
- **Mechanically controlled yarn:** a closable hook, paired supports, guided yarn
  presentation and a gravity/counterweight feeder.
- **Reproducible calculations:** complete moving-mass accounting, force balance,
  finite-radius cord routing and explicit motion coordinates.

[Full assembly STEP](cad/r5m2/generated/integrated_rigid_fixture.step) ·
[Individual parts](cad/r5m2/generated) ·
[Design inputs](spec/r5_m2_fixture.json) ·
[Engineering notes](docs/ENGINEERING.md)

## Run it

Use Python3.12 and a virtual environment:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r cad/r5m2/requirements.lock.txt
.venv/bin/python cad/r5m2/build.py
.venv/bin/python examples/feeder.py
.venv/bin/python -m unittest discover -s tests -v
```

The build exports native solid geometry and part meshes. All CAD lengths are in
millimetres. The examples execute numerical design checks; the hardware is a
research prototype being developed toward physical stitch demonstrations.

## Current design

Revision **R5-M2-D22** uses a42mm head offset for rotating-tool clearance and
finite-radius cord geometry shared by the feeder calculation and CAD. A component
mass model accounts for the complete moving assembly and its ballast allocation.
D22 uses an8.25mm shaft advance,16.75mm return and a barrel ending12mm behind
the tool datum, with explicit conditional loop-clearance calculations.

Created by [arushis1212](https://github.com/arushis1212).
See [research references](docs/REFERENCES.md) for the textile and mechanics work
that informs this project.

## Strand mechanics

The numerical toolkit includes a planar extensible-rod model with large-angle
bending and finite-radius contact. Analytic stretch/cantilever checks, energy
gradients and continuous clearance bounds are covered by executable tests.
Run `.venv/bin/python examples/rod_energy.py` for a minimal reference case.

The toolkit also includes [three-dimensional CAD contact and strand mechanics](docs/STRAND_MECHANICS.md), with analytic and solid-model regression checks.

[Loop-holding mechanics](docs/LOOP_HOLDING.md) couples yarn contact to clamp force, torque and neighboring textile load paths.

[Mechanically guided loop transfer](docs/LOOP_TRANSFER.md) adds a sloped pocket exit, paired restraint plates and a guided two-pin lift, with editable solid geometry.

[Material length and contact integration](docs/CONTACT_INTEGRATION.md) documents spatial quadrature and conservative motion bounds, with executable regression examples.

[Coupled equilibrium and contact algorithms](docs/NUMERICAL_METHODS.md) describe the banded-clamp solver, exact contact broad phase and adaptive interpolation certificates.

The [T15 transfer station](docs/LOOP_TRANSFER.md) adds an installed bracket and mechanically stopped pin shuttle. Its [557-solid assembled STEP](cad/transfer/installed/installation.step) and [nominal position checks](docs/INSTALLED_GEOMETRY.json) accompany the editable design.

[Connected yarn mechanics](docs/CONNECTED_YARN.md) adds an explicit material chain, shared-clamp force balance and hollow-guide contact, with reproducible numerical checks.

[Upstream feeder mechanics](docs/FEEDER_DOMAIN.md) introduces conserved material lengths, exact counterweight virtual work and native-geometry contact checks.
