# Exposing a captured crochet loop

The closed hook carries the old loop in its heel and a fold of working yarn in its nose. To expose that fold, Roche stops the hook 3.06050 mm into its fourth return translation and withdraws the yarn guide by **0.48 mm**. In the nominal simulation, the entire 0.60 mm yarn cross-section clears the guide face by **0.24830 mm**. The nearest nonadjacent strand is **0.31675 mm** away, measured surface to surface. Both feeder nips hold the same material marks during the motion.

## Tool coordinates

Positions are in the machine world frame. Hook travel is accumulated distance along its straight segments after closure. The hook stays at +30° inclination and 270° roll with the sliding gate at its 0 mm closed datum. The fourth segment ends at 12.03593 mm on the selected trajectory. The last row moves only the guide.

| Hook travel (mm) | Guide withdrawal (mm) | Hook XYZ (mm) | Guide XYZ (mm) |
| ---: | ---: | --- | --- |
| 0.00000 | 0 | 136.14081, 166.66927, 84.47375 | 136.00000, 164.62830, 87.30221 |
| 2.03667 | 0 | 138.01664, 166.17199, 83.85569 | 136.00000, 164.62830, 87.30221 |
| 4.89805 | 0 | 140.26664, 164.46446, 83.39816 | 136.56250, 162.97346, 86.69989 |
| 8.97543 | 0 | 139.51664, 160.87535, 85.18165 | 136.37500, 164.62830, 87.30221 |
| 12.03593 | 0 | 139.05641, 159.38384, 87.81419 | 136.25994, 165.49324, 87.61702 |
| 12.03593 | 0.48 | 139.05641, 159.38384, 87.81419 | 136.25994, 165.94430, 87.78119 |

The guide is stationary on the first segment. During the second it follows one quarter of the hook's X displacement while advancing axially from 27.00000 to 28.76104 mm. It retracts to 27.00000 mm on the third segment and continues tracking the hook until the selected stop. The final withdrawal follows the guide's own axis, tilted 20° above the horizontal.

## Reproduce the motion and measure the result

Run these commands from the repository root. The interpolation uses the Python standard library. The clearance calculation uses NumPy from the CAD environment.

```sh
python3 -m examples.closed_hook_return
python3 -m examples.closed_hook_return --guide
python3 -m examples.closed_hook_return --guide --withdraw 0.48
python3 -m examples.closed_hook_return --measure
```

For hook or guide coordinates between stations, pass a hook travel in millimetres, such as `--guide 3.0`. The `--reference` option prints the four complete reference translations. The JSON includes the local yarn centerlines and the triangle spanning the foundation opening. The measurement intersects the working strand with that triangle, projects the intersection onto the guide axis and subtracts the yarn radius. It also calculates the exact minimum distance between the neighboring finite yarn segments and subtracts their combined radii. [Coordinates and local geometry](../examples/closed_hook_return.json) · [Interpolator and clearance calculation](../examples/closed_hook_return.py) · [Regression tests](../benchmarks/test_closed_hook_return.py)

## Modeled stopping range

With the hook fixed at the selected position, a guide withdrawal of **0.43–0.70 mm** maintained at least **0.2068 mm** of whole-radius sleeve clearance and **0.3166 mm** of clearance to the nearby foundation segment on the continuous modeled path. The lower bounds account for motion between the sampled equilibria. The nominal 0.48 mm setting sits 0.05 mm above the lower end of this guide-only command range.

The simulation uses 330.98634 mm of working yarn between the registered cloth and closed outlet, with nominal axial rigidity 2 N and bending rigidity 0.02 N·mm². At 0.48 mm, calculated peak tensile strain is **2.584%** and combined outlet grip demand is **0.14645 N**. These are quasistatic model results for that yarn specification. Fixture repeatability, yarn properties and physical trials determine prototype performance.
