# Roche

**Crochet through mechanical registration.**

Roche explores how constrained yarn paths and repeatable tool motions can handle
a deformable material without cameras. The first application is a manually
actuated research prototype for stitch and swatch development.

[![CAD views of the complete Roche machine and its stitch station, with the hook in orange, support bed in gold, and transfer mechanism in teal](docs/images/assembly.png)](cad/machine/generated/machine.step)

*Both views use the same assembly pose. The detail shows how the closable hook (orange) sits beside the paired supports (gold) and transfer mechanism (teal).*

The current **D26-T17-S3-indexed-candidate** design contains **692 installed native solids**.
It combines a closable hook, four paired-support stations, an indexed transfer
module, a gravity feeder, two retained service nips and a hanging fabric clamp.
Printed structural parts work with machined metal yarn-contact tools and
purchased fasteners and bearings.

- [Complete assembly STEP](cad/machine/generated/machine.step)
- [Individual manufacturing profiles](manufacturing/current/cad)
- [Parts register](docs/manufacturing_parts.csv)
- [Machine inputs](spec/current_machine.json)
- [Engineering and mechanics](docs/ENGINEERING.md)
- [Elastic interface benchmarks](docs/ELASTIC_INTERFACES.md)
- [Convex search methods and benchmarks](docs/CONVEX_SEARCH.md)
- [Bounded quadratic solvers and analytical tests](docs/BOUNDED_QUADRATIC.md)
- [Contact integration and analytical refinement](docs/CONTACT_INTEGRATION.md)
- [Unilateral contact and friction benchmarks](docs/UNILATERAL_CONTACT.md)
- [Newton contact solver and analytical tests](docs/SEMISMOOTH_CONTACT.md)
- [Hex-drive fit and tolerance benchmark](docs/HEX_DRIVE_FIT.md)
- [Research references](docs/REFERENCES.md)

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r cad/r5m2/requirements.lock.txt
.venv/bin/python -m cad.r5m2.build
.venv/bin/python -m cad.transfer.build
.venv/bin/python -m cad.machine.assembly
.venv/bin/python examples/feeder.py
.venv/bin/python examples/rod_energy.py
.venv/bin/python -m unittest discover -s tests -v
```

The code regenerates native CAD and executes mechanics examples. Numerical
examples declare their benchmark material properties; component measurements
and physical stitch trials establish application performance.

Created by [arushis1212](https://github.com/arushis1212).
