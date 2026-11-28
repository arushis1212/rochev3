# Indexed cloth-support bearing

A 1.00 mm round steel tooth carries the older stitch on the near rail of the transfer fork. The tooth pivots about a 0.32 mm spindle. A 0.24 mm transverse indexing pin engages the hub at either end of its 90° turn. Pulling the pin 0.470 mm releases the hub. Its two flanged sleeves carry radial and axial loads. The STEP solids use the same world frame and millimetres.

The example includes two simulation inputs. The draw sample supplies the measured yarn force and contact location for the peak index-pin load. A separate four-crossing yarn configuration supplies the two old loops for the cast-off calculation.

| Measurement | Nominal model result |
|---|---:|
| Peak index-pin normal force in the draw sample, including rotor weight | 0.03900 N |
| Peak journal pressure in that load case | 0.5730 MPa |
| First retained loop clears the fork plane | 3.77436 mm withdrawal |
| Second retained loop clears the fork plane | 23.85304 mm withdrawal |
| Entire fork stroke | 29.70176 mm |
| Continuous tooth-to-yarn lower bound during swivel | 0.07429 mm |
| Smallest tooth-to-yarn gap during withdrawal | 0.01528 mm |
| Smallest original fork-to-yarn gap during withdrawal | 0.000494 mm |

From the repository root, run `python -m examples.indexed_latch` for the load and release calculation. Add `--native` with CadQuery installed to measure both indexing positions, the swivel and full withdrawal directly from the supplied STEP solids and yarn coordinates. Run `python -m unittest benchmarks.test_indexed_latch` to reproduce the numerical checks.

For the swivel, each midpoint clearance loses the maximum possible surface motion within its 1° interval. For withdrawal, each stationary yarn edge sweeps an exact parallelogram in the translating fork frame. The model uses a 0.300 mm circular yarn radius. These values describe the registered nominal geometry. The fork’s smallest clearance is 0.494 µm, so manufacturing requires a separate fit and yarn-variation budget.

`push_pull_tool.step` is a two-tined tool that engages the turned groove in the indexing pin. `turn_tool.step` fits the slot on the opposite end of the spindle. The pin seats before the turning tool leaves the spindle. The supplied STEP solids can be inspected individually or loaded together as an assembly.

## Spring-brake version

The `brake/` directory contains a replacement fork, rotor and pin for the cam-driven slide. The 1° tapered pin locates both sides of either seat. The normal force on the pin changes direction during deceleration. In the two recorded brake samples it spans +1.682 to −25.095 mN. Native solid intersections at both +0.02° and −0.02° verify that either direction meets the seated pin.

A 31.829 mg integral tab on the tail brings the modelled moving fork assembly to the cam design mass of 4.458686 g and aligns its transverse centre of mass with the 0.800 mm pushrod. The crossbolt and adhesive are included for mass-property replay. The rod engages a 3.000 mm bonded length. A fivefold axial test load corresponds to 0.8712 MPa of average interfacial shear.

Run `python -m examples.indexed_latch --brake --native` to calculate the assembly mass and transverse offset from the actual solids, replay the two brake loads, test seating in both directions, and measure clearance against the same cast-off yarn.

## Relieved heel

The 40° relief moves the heel away from the withdrawing yarn while preserving the working face of the deployed tooth. Across the specified machining tolerances, the registered 0.600 mm diameter yarn has 0.040954 mm of clearance over the 29.701763 mm withdrawal. The CAD benchmark also checks the earlier loaded yarn and the bearing sleeves. [Dimensioned variant and reproduction](relieved/README.md)
