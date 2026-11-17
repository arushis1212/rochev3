# Roche

**Crochet through mechanical registration.**

Roche explores how constrained yarn paths and repeatable tool motions can handle a deformable material without cameras. The first application is a manually actuated research fixture for stitch and swatch development.

The current D24 design includes84 parametric component variants, native STEP/STL files, a closable hook, paired loop supports, a gravity feeder and a hanging clamp with a finite return around a smooth captured pin. The installed transfer configuration has558 nominal solids.

- [Parametric dimensions](spec/r5_m2_fixture.json)
- [Assembly STEP](cad/r5m2/generated/integrated_rigid_fixture.step)
- [Individual parts](cad/r5m2/generated)
- [Engineering and reference configuration](docs/ENGINEERING.md)
- [Research references](docs/REFERENCES.md)

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r cad/r5m2/requirements.lock.txt
.venv/bin/python cad/r5m2/build.py
.venv/bin/python examples/feeder.py
.venv/bin/python -m unittest discover -s tests -v
```

The numerical toolkit includes elastic rods, finite-radius contact, rigid-clamp virtual work and collision-aware solver steps. Examples use explicit benchmark material properties. Hardware is a research prototype being developed toward physical stitch demonstrations.

Created by [arushis1212](https://github.com/arushis1212).
