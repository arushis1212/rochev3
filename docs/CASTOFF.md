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

A second fixture begins with the jaw holding the material between two specified fabric-neck positions. The seven-part shuttle advances the two physical shafts by 6 mm. After 1.120 mm of presentation travel, the pins each carry about 1.765 mN while the jaw and hook still grip the strand. Eighteen force stations and their intervening motion checks cover transfer to pin-only support. The tool then withdraws 4.800 mm and clears the yarn by at least 0.0466 mm over that withdrawal. The stored measurements include the required endpoint loads and the same material mark throughout. [Forward reload measurements](../cad/castoff/pin_release.json)

## Replaying release from the original eye

The closed receiving jaw holds material mark 1073.000 mm while the original eye opens 90° and moves away. Five finite rectangular sections span the original eye. By 16.869359 mm of commanded payout all five sections are empty. At that station the receiving hook and jaw exert normal loads of 11.526 mN and 11.091 mN in the nominal model. The friction coefficient is 0.24. The listed forces include the inertia of the moving yarn.

Run `python3 examples/eye_release.py` to intersect the material segments with each section in the moving eye frame. The input includes every segment whose bounding box lies within 0.05 mm of the aperture box at the sampled stations. It also records the distance to the nearest excluded segment. [Section geometry, yarn coordinates and opposite-face loads](../cad/castoff/eye_release.json)

The modeled feeder uses three pulleys and a free carriage. Its 259 saved states reconstruct the outlet history, including 113 intervals while the loaded jaw and eye move. The final feeder force residual is 0.0000276 mN at 16.875271 mm payout. The 733-part station includes the opened eye and the closed receiving jaw. Outlet travel is prescribed; the model solves the carriage height.
