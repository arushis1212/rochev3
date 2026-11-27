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

## Following two yarn marks through the foundation

Imagine marking each leg of the working fold just outside the foundation opening before the hook starts pulling. Both marks pass through the opening during the modeled return. The amount of yarn between the two penetrations, measured along its unstretched material coordinates, grows from **9.85042 to 21.80342 mm**. The old loop stays in the heel and the fold stays in the nose.

| Yarn mark (mm from material origin) | Hook travel at each passage (mm) | Final forward clearance (mm) |
| --- | --- | ---: |
| 1024, cloth side | Forward at 4.21256, back at 6.02704, forward at 6.48050 | 0.1960 |
| 1040, feeder side | Forward at 7.73928 | 2.9055 |

The example tests each mark’s trajectory against the triangles spanning the actual foundation yarn on 190 linear motion intervals. At all four crossings the marked yarn clears the foundation rim by at least 2.11368 mm, accounting for both yarn radii. Final forward clearance measures how far the entire marked yarn section lies in front of all foundation-rim fibers along the machine Y axis. Five sections through each hook pocket independently track retention.

```sh
python -m examples.first_draw
python -m unittest benchmarks.test_first_draw
```

The motion comes from the 719-component hook-and-feeder configuration. The compressed data contains the material labels, yarn coordinates, oriented aperture and hook coordinates from registered capture to the selected return stop. This example covers the first draw of a nominal simulated stitch. [Motion coordinates](../examples/first_draw_motion.npz) · [Geometric replay](../examples/first_draw.py) · [Tests](../benchmarks/test_first_draw.py)

## Parking the guide

After the guide exposes the fold, the new yarn remains in the closed hook's nose and the old loop remains in its heel. The guide retracts along its inclined axis, pauses while the hook backs away, finishes retracting, then centers on X. The guide reaches machine coordinates (136.00000, 190.00000, 96.53675) mm with the feeder outlet closed throughout.

| Phase | Moving tool | Distance from start of phase, mm | Other tool |
|---|---|---:|---|
| Guide starts withdrawing | Guide along its 20° axis | 17.245000 | Hook held |
| Hook backs away | Hook along its preceding draw line | 0.793463 | Guide held |
| Guide finishes withdrawing | Guide along the same axis | 8.354545 | Hook held |
| Guide centers | Guide along negative X | 0.259943 | Hook held |

The distance clock starts at zero for each phase. In the nominal simulation, the working yarn maintained at least 0.13993 mm of surface clearance from the previously formed yarn over 127 motion intervals. All three marks used to track the first draw stayed on the drawn-through side of the foundation opening. At park the surface gap between the nearest working and foundation-rim segments is 0.368369 mm. The example independently calculates this endpoint measurement from four recorded strand vertices and the 0.600 mm yarn diameter. [Parking coordinates and yarn sample](../examples/guide_parking.json) · [Replay and distance calculation](../examples/guide_parking.py)

Run from the repository root with Python 3.9 or later. The commands print all phase endpoints, sample the hook 0.4 mm into its own movement, then measure the yarn gap.

```sh
python3 -m examples.guide_parking
python3 -m examples.guide_parking hook-backoff 0.4
python3 -m examples.guide_parking --measure
python3 -m unittest benchmarks.test_guide_parking
```

## Station one holder

An alternative holder for the first support station seats two M2 fasteners and their nuts. Its 9 mm gate-opening stroke clears the installed geometry in the nominal parked configuration. The holder and four fastener parts also clear the moving assembly and all 995 yarn segments in each of the 190 return and 127 parking intervals. The smallest modeled yarn clearance to these five parts is 0.02070 mm during return and 0.35838 mm during parking. These values describe the nominal geometry. [Per-interval clearance bounds](../examples/station_one_holder_clearances.csv)
