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

## Pin load transfer

A local yarn model holds the two fabric-neck positions fixed while the jaw transfers tension to the two pins. The jaw first holds the live material 0.015 mm above its relaxed seat. At that position the jaw face carries 4.853 mN, the opposing hook face carries 5.232 mN and the pins carry 58.614 and 58.602 mN. Lowering the jaw in 0.003 mm increments transfers its remaining load. The pins then carry 58.023 and 58.011 mN while the jaw opens 75°, its gate opens 90° and the tool withdraws 2.700 mm. The free-coordinate force error is below 0.001 mN at all six stations. The two specified neck positions supply approximately 30 mN each. [Station loads, fabric boundary conditions and release commands](../cad/castoff/pin_release.json)
