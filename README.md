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
- **522 assembly solids:** tooling, positioning stages, support bank, feeder,
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

Revision **R5-M2-D21** uses a42mm head offset for rotating-tool clearance and
finite-radius cord geometry shared by the feeder calculation and CAD. A component
mass model accounts for the complete moving assembly and its ballast allocation.

Created by [arushis1212](https://github.com/arushis1212).
See [research references](docs/REFERENCES.md) for the textile and mechanics work
that informs this project.

## Strand mechanics

The numerical toolkit includes a planar extensible-rod model with large-angle
bending and finite-radius contact. Analytic stretch/cantilever checks, energy
gradients and continuous clearance bounds are covered by executable tests.
Run `.venv/bin/python examples/rod_energy.py` for a minimal reference case.
