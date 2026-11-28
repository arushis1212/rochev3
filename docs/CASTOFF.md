# Station-one cast-off

The open fork withdraws between two retained loops after the second yarn presentation. The signed crossing of each loop through the fork frame gives its release coordinate. The included example reads the three-dimensional yarn centerlines and the installed fork axes from a stationary four-crossing configuration.

| Event | Fork withdrawal |
| --- | ---: |
| L1 exits the frame | 4.110954 mm |
| L0 exits the frame | 23.831232 mm |
| Slide reaches the retracted stop | 29.701763 mm |

The modeled sequence opens the crossbolt by 10 mm, disengages the index screw by 1.2 mm, withdraws the fork and relocks the slide. The finite-component sweep at this yarn geometry has at least 0.186 mm of yarn clearance and 0.220 mm to unrelated hardware.

The two reload pins have 1.50 mm diameter and 6.60 mm center spacing. Inflating each pin by the 0.30 mm yarn radius and the 0.20 mm positioning allowance gives the necessary centerline enclosure perimeter `2d + 2πr = 21.054 mm` and width `d + 2r = 9.100 mm`. The example reports the measured outside arc and straight neck closure so that the required loop expansion can be calculated for this configuration.

Run `python -m examples.castoff` with NumPy from the repository root. The example reproduces geometric events on the supplied centerlines. [Registered coordinates](../cad/castoff/geometry.json) · [Calculation](../examples/castoff.py)
