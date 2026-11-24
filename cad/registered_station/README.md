# Registered crochet head and station

Open [P5_REGISTERED_ASSEMBLY.step](P5_REGISTERED_ASSEMBLY.step) directly in a STEP assembly reader. The file places the steel hook, brass slide, roller station, guide and stripping frame, retained spring tips, support cover and base board in a common coordinate frame. The 257 named members include machined pieces, purchased hardware, bonding material and three clearance envelopes. The file uses millimetres. [PARTS.json](PARTS.json) lists each member’s name, function, geometry and position.

To inspect the yarn-facing head, isolate `TOOL_H01_hook_body`, `TOOL_H02_gate`, `TOOL_H03_barrel_stop` and `stand_bearing`. To inspect the mount, isolate `local_register_frame`, `stand_receiver`, `F03_receiver_drilling`, and parts prefixed `hard_stop_`, `GN615_` or `fitted_pin_`. The slide is indexed in the P5 pose. The three spring leaves are shown in their manufactured, unloaded shape.

The brass gate has a transverse recess with a nominal depth of 0.125 mm. A Ø6.35 mm tool forms it from the unshifted part datum. The STEP uses the middle rigid head setting with one 0.0508 mm foil. The other 256 members retain their original geometry and placement. [Machining and fitting the gate](INSTALL_GATE.md) · [CAD exchange measurements](GATE_EXCHANGE.json)

[Gate milling and inspection fixtures](../gate_inspection/README.md)

## Install the register

1. Machine the frame from 6061-T6 to the supplied solid. Its envelope is 108 × 87 × 5.5 mm. Tap the two front holes M3 × 0.5 along Y at X 204 and 265, Z 15.3. Tap the right stop hole M3 × 0.5 along X at Y 73, Z 15.0. The three opposing plunger axes are at Z 14.75. Use M4 × 0.7 threads there. Inspect all threaded bores and mating screws using the intended threads. The CAD represents their major diameters.
2. Prepare the receiver with its three Ø4.04 × 2 mm blind pockets. Seat hardened Ø4 × 2 mm steel buttons flush on their back faces and retain them radially. Fit each Ø4 × 14.1 mm dowel into the frame with 0.002–0.006 mm of measured diametral interference. Press with the surrounding frame supported. The four frame-pin centers in XY are (188, 67.5), (284, 67.5), (209.5, 32.5) and (259.5, 32.5).
3. Prepare the revised 12 mm board using its STEP geometry. It has four Ø7 × 9 mm blind potting sockets at the pin locations. Center the receiver in its M4 counterbores, fixture the ring on the board at Z 12 and cast the projecting dowels in the sockets. Cure to the selected adhesive's specification. Assemble the frame’s four M4 × 25 bolts, nuts and flat washers. Check frame seating and board condition after cure.
4. Fit the Ø2 mm flat-ended M3 × 20 adjustment screws and the M4 spring plungers. The front two screws set translation and yaw. The right screw sets the side position. Set each spring plunger for 0.40 mm projection at nominal assembly. Verify its force is 6–14.5 N throughout the intended adjustment interval. Check hardened buttons after a proof load. [Plunger dimensions and nominal loads](https://live-katalog.ganternorm.com/pdf/ganter/EN/615.pdf?dispositiontype=attachment)
5. Assemble the 4.500 mm reference strip with a single 0.0508 mm foil. Seat the foot, post and roller yoke. Center the four existing receiver M4 × 20 clamps to within 0.15 mm radial offset at each head. Turn both front jacks equally to adjust Y and adjust their difference to correct yaw. One degree is 1.389 µm of screw advance. Hold each jack while tightening its jam nut. Tighten the receiver clamps diagonally. Qualify retained clamp force on a representative board stack and use at least 20 N per clamp. Measure the station with the assembly loaded after locking.
6. For removal, unload the station with the powered cam in its full-open 196°–217° dwell. Remove the M4 foot lock, translate the foot +7 mm along machine Y, then +58 mm along X. Support and lift the station. For the installed receiver register, the calculated minimum nominal stock clearance on this path is 0.300 mm.

## Gauge the loaded roller

The station target is +0.0508 mm in machine Y relative to the zero-foil position, with ±0.005 mm equivalent-Y allowance. A flat-ended screw contacts the receiver on each hard datum. The roller itself is the working reference. Its contact normal has Y component −0.218926, so the entire allowed displacement in the normal direction is only ±1.09463 µm.

Use a calibrated, low-force tactile comparator and a master certified relative to the installed head datum. Reach the free side of the loaded bearing along (0, −0.218926, −0.975741). The middle contact point is at (132.766641, 90.027713, 96.003899) mm. Also sample at X offsets −1.20 and +1.20 mm. A Ø1 mm spherical tip, Ø0.70 mm stem, Ø3 mm shank and Ø12 mm pickup-body envelope has 0.425 mm minimum clearance at the side tracks during 4 mm of retraction. Confirm the actual instrument and holder fit. Retract before running the machine.

Measure a master, then the station, then the master again. Correct for the time-interpolated master reading and the difference in actual loaded directional diameters between the two bearings. Characterize race runout, alignment, diameter changes with load, edge profile, temperature and the installed head datum. Record residual face error within ±0.25 µm with independently established uncertainty bounds totaling at most 0.79 µm. Repeat with the real operating load, a 2 N proof load, both approach directions and after removal and reinstallation. These figures define the commissioning test. [NIST study of contact deformation in dimensional comparison](https://www.nist.gov/publications/deformation-gauge-blocks)

## Calculated operating envelope

The rigid-body model retains at least 4.018 N of compression at each hard stop under a 2 N upper roller normal load, up to 0.4 N tangential load, and the specified spring forces. The aluminum frame model predicts 0.0310 µm maximum incremental Y displacement at the roller for ideal fixed pin walls. The tactile measurements include physical wood, cured joints, bearing compliance and assembly variation. Dimensions, assumptions, CAD exchange checks and receiving limits are in [CHECKS.json](CHECKS.json).

