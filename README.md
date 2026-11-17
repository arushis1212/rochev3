# Roche

**Crochet through mechanical registration.**

Roche explores how constrained yarn paths and repeatable tool motions can handle a deformable material without cameras. The first application is a manually actuated research fixture for stitch and swatch development.

The current D25 / T16 design includes 85 base component variants and a 566-solid installed assembly. A closable hook, paired loop supports, gravity feeder and hanging clamp work together around a controlled yarn path. The return strand can deform around a smooth captured pin between two defined gripping lands.

- [Parametric dimensions](spec/r5_m2_fixture.json)
- [Installed assembly STEP](cad/transfer/installed/installation.step)
- [Individual parts](cad/r5m2/generated)
- [Parts register](docs/manufacturing_parts.csv)
- [Mechanics and reference configuration](docs/ENGINEERING.md)
- [Research references](docs/REFERENCES.md)

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r cad/r5m2/requirements.lock.txt
.venv/bin/python cad/r5m2/build.py
.venv/bin/python cad/transfer/build.py
.venv/bin/python cad/transfer/installation.py
.venv/bin/python examples/feeder.py
.venv/bin/python -m unittest discover -s tests -v
```

The numerical toolkit includes elastic rods, finite-radius contact, rigid-body virtual work and collision-aware solver steps. Examples use explicit benchmark material properties. Hardware is a research prototype being developed toward physical stitch demonstrations.

Created by [arushis1212](https://github.com/arushis1212).
