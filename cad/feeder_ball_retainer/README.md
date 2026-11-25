# Formed foil retainer for the 0.600 mm feeder

A steel spring shoe bears on a 0.500 mm ball seated in a 45° cup. This T-shaped stainless foil surrounds the exposed side of the ball and retains it during unloads. A countersink provides clearance around the working sphere while the cylindrical pilot limits its escape. [Retainer STEP in installed coordinates](FRONT_RETAINER.step) · [Dimensions and receiving limits](SPEC.json)

| Dimension | Nominal size |
|---|---:|
| T stem and head widths | 0.550 and 0.920 mm |
| Stainless foil thickness | 0.050 mm |
| Cylindrical pilot | Ø0.460 mm |
| Spotting angle and axial depth | 90° included × 0.036 mm |
| Nominal ball-facing mouth | Ø0.532 mm |
| Cup shim at the 0.600 mm station | 0.0127 mm |

Support an oversize piece of foil against sacrificial stock. Drill the pilot, spot from the ball side in the same setup, then release the T outline. Section a setup witness to measure the shoulder depth and angle. Check pilot diameter, offset, edge quality, throat continuity and the installed center relative to the seated ball. The tolerance stack includes eccentricity, tilt, edge form and ball size. [Shim-stock tolerances](https://www.trinitybrand.com/tbi-technical-information/) · [0.460 mm drill](https://guhring.com/ProductsServices/SizeDetails?EDP=9038990004600)

The nominal CAD clearance is **0.029037 mm** at the closest pose of a 1,703-sample guided-shoe simulation. With the receiving limits in SPEC.json and ball-center travel within 0.004 mm radially and downward, the analytical clearance bound is **0.002644 mm**. Avoiding both intact retaining rings at the 0.090 mm radial escape boundary would require a plane separation of 0.393800 mm. The maximum specified spacing is 0.328333 mm.

Run `python3 check_fit.py` here to reproduce the dimensional calculation using standard Python. The nominal simulation and tolerance calculation describe this individual mechanism. [Matched feeder and spring-carrier calculations](../../docs/YARN_HANDOFF_FIXTURES.md)
