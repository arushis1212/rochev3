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
