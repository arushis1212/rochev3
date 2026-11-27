# Closed-hook return path

The swatch fixture commands the hook through four straight translations after the gate closes. The hook stays at 270° roll and the gate stays at its closed datum. A machinist can use the coordinates to compare tool-tip positions against the machine frame. Distances in the first column accumulate along the bends in the path.

| Travel from closure (mm) | X (mm) | Y (mm) | Z (mm) |
| ---: | ---: | ---: | ---: |
| 0.00000 | 136.14081 | 166.66927 | 84.47375 |
| 2.03667 | 138.01664 | 166.17199 | 83.85569 |
| 4.89805 | 140.26664 | 164.46446 | 83.39816 |
| 8.97543 | 139.51664 | 160.87535 | 85.18165 |
| 13.96291 | 138.76664 | 158.44475 | 89.47172 |

Run `python3 -m examples.closed_hook_return` from the repository root to reproduce the table, or append a distance in millimetres to evaluate an intermediate position. The calculation describes commanded hook geometry. Yarn motion, contact loads and actuator calibration have separate measurements. [Coordinate data](../examples/closed_hook_return.json) · [Interpolator](../examples/closed_hook_return.py)

## Guide motion through the second waypoint

The yarn guide holds its position for the first 2.03667 mm of hook travel. During the next 2.86138 mm, the guide moves 0.56250 mm in X, a quarter of the hook’s X displacement. Its axial command advances from 27.00000 to 28.76104 mm. The simulated feeder clamps the same material mark throughout this command.

| Hook travel (mm) | Guide X (mm) | Guide Y (mm) | Guide Z (mm) |
| ---: | ---: | ---: | ---: |
| 0.00000 | 136.00000 | 164.62830 | 87.30221 |
| 2.03667 | 136.00000 | 164.62830 | 87.30221 |
| 4.89805 | 136.56250 | 162.97346 | 86.69989 |

Run `python3 -m examples.closed_hook_return --guide` for the guide positions, or add a hook travel such as `3.0` to interpolate between them.
