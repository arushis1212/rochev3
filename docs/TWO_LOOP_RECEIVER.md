# Receiving two yarn loops

After the first draw and guide parking, the previous loop sits in the heel of the main hook and the newly drawn loop sits in its nose. Their openings face different directions. An inclined receiver can enter both while the main hook stays closed and the supply outlet holds the same registered length of yarn.

The probe example uses a 1.50 mm diameter needle and a 0.60 mm nominal yarn diameter. Over the finite approach, the needle surface clears the yarn by 0.951 mm and the nearest installed hardware by 1.527 mm. The example recomputes the yarn distance from the stored polylines. The hardware number uses the axis-to-solid distance measured in the fitted assembly.

The closing receiver pairs that needle with a 2.10 mm diameter return finger. The fingers are 10 mm apart. After 29.702 mm of insertion, a transverse pin closes the opening. The nominal sweep includes the bridge, return finger, gate boss and pin. With collars, a slide lock and two braces fitted, the swept assembly clears the yarn by at least 0.810 mm and the other hardware by at least 0.749 mm in the nominal model.

| Yarn passing through the closed receiver face | Material coordinate along the yarn |
| --- | ---: |
| Previous loop | 901.714 mm |
| Newly drawn loop | 1038.947 mm |

The fixture preserves each yarn point’s original material coordinate. Counting intersections of the physical yarn with the receiver opening distinguishes a threaded strand from a needle that merely appears inside the loop in one view. The main hook still supports both loops at this pose. Transfer of their load during hook withdrawal is a separate operation.

Run the geometry measurement and its regression checks from the repository root.

```sh
python -m examples.receiver_probe
python -m unittest benchmarks.test_receiver_probe
```

The bed carries a separate rear indexing pin. Its storage hole lets the operator withdraw the pin while the head and guide stay at the two-loop pose. [Rear index dimensions, STEP files and operating sequence](../cad/station_one/REAR_INDEX.md)

## Parts in the receiving pose

The files share the machine coordinate system. The carriage is indexed at zero and the receiver is fully advanced, with its screw and slide lock seated. The modeled thread cylinders give the major diameters. The M1 × 0.25 crossbolt travels 10 mm in 40 turns. The primary needle has a 1.15 mm smooth clearance bore and the return finger carries the tap.

| Part | Machine-frame geometry |
| --- | --- |
| Receiving fork and keyed slide | [STEP](../cad/station_one/S1-01-receiving-fork.step) |
| Transverse M1 screw | [STEP](../cad/station_one/S1-02-M1-crossbolt.step) |
| S1 holder, braces and slide guide | [STEP](../cad/station_one/S1-03-holder-braces-guide.step) |
| M2 slide-lock screw | [STEP](../cad/station_one/S1-04-M2-index-dog.step) |

## How much load reaches the receiver?

At a gate opening of 2.060672 mm, the drawn bight rests against the 1.50 mm diameter needle of the locked receiver. In this stationary simulation the needle carries 3.227 mN. The hook body retains several contacts with a total normal load of 82.045 mN. The sliding gate carries zero normal load. These are sums of contact magnitudes at each component, so their ratio does not measure a fraction of the yarn tension.

Run the example from the repository root with NumPy and SciPy installed.

```sh
python -m examples.receiver_load
```

The example includes every free node of the working strand, the two fixed endpoint tangents, yarn rest lengths, axial and bending stiffnesses, gravity weights, material marks, and CAD contact normals. It differentiates the elastic energy, adds gravity, and finds nonnegative normal reactions that balance the free nodes. It also measures the radial distance between the loaded yarn and the needle. The maximum absolute component of the residual is 0.043 nN. This benchmark evaluates a stationary pose under nominal frictionless contact. [Executable example](../examples/receiver_load.py) · [Numerical inputs](../examples/receiver_load.npz)

With the receiver locked, advancing the guide by 5.264977 mm along the programmed presentation direction raises the simulated needle reaction to 7.167 mN. The same finite yarn retains its material coordinates across the sampled guide settings. Reproduce the second stationary balance with the following command. [Guide-advance data](../examples/receiver_load_guide.npz)

```sh
python -m examples.receiver_load examples/receiver_load_guide.npz
```

## When both strands move

The handoff simulation starts at 1.005843 ms with 122 free nodes in the working strand and 114 free nodes in the foundation loop. The feeder outlet is closed and the fork is locked. At 1.030843 ms the strands push against each other. At 1.334055 ms the working strand first loads the receiving needle. Over the 132 accepted steps through 2.500 ms, the foundation moves as much as 1.194 mm and the working strand moves as much as 3.370 mm. At the final sample the needle carries 6.306 mN.

The benchmark reconstructs nodal acceleration from the position history and the initial velocity. It balances inertia, elastic restoring forces, gravity and support forces against nonnegative contact reactions. At each yarn contact it locates the closest points on the two moving segments and distributes equal and opposite normal forces to their four nodes. The maximum free-node force component left unbalanced is 0.966 µN or less. The needle receives a normal impulse of 4.999 µN·s over this interval. These values describe the nominal frictionless model with prescribed material outside the two modeled spans. [Replay the transient](../examples/mobile_yarn_contact.py) · [Registered motion and force inputs](../examples/mobile_yarn_contact.npz)

```sh
python -m examples.mobile_yarn_contact
```

## Presenting fresh yarn from the side

A separate side-entry cartridge approaches the strand while the original head is parked and the receiver holds both loops. Its fixed hook blade and sliding gate run in two short guide lands. The simulated 3.5 mm entry brings fresh material to all five transverse sections of the nose after 1.920 mm of travel. A 5.75 mm gate stroke closes the pocket. The material at the middle section is 1054.000 mm along the registered yarn. The finite blades and housing clear the yarn by at least 0.4199 mm through entry and closure, with the closed feeder and receiver in their modeled positions.

The example reconstructs the crossing intervals from the 3D yarn coordinates, section windows and cartridge orientation. The setup is a nominal geometry study of a stationary loaded receiver with a separately positioned cartridge. [Replay the side entry](../examples/side_entry.py) · [Material and frame data](../examples/side_entry.npz)

```sh
python -m examples.side_entry
```

At 1.400 mm of nominal withdrawal, the secondary gate carries 0.8823 mN and the receiving fork carries 2.9725 mN. The stopped model balances the free working yarn to 0.065 nN with all five sections still occupied. At 1.750 mm, the secondary gate carries 3.484 mN and the original receiver carries 2.244 mN. The registered motion between these stopped poses clears 726 component models and preserves both receiver passages. The closest housing-to-carriage spacing during entry lies between 0.0371 and 0.0406 mm in the nominal CAD. The three component models define the cartridge geometry used in this calculation. [Hook blade](../cad/side_entry/S1-aux-hook.step) · [Sliding gate](../cad/side_entry/S1-aux-gate.step) · [Housing](../cad/side_entry/S1-aux-barrel.step)

## From receiver contact to pickup

The same simulated strand now travels from the parked handoff into the second hook. The open cartridge approaches diagonally by 4.230 mm. While the receiver accepts load, its secondary gate continues closing at 20 mm/s. At the first receiver contact, 1.334 ms after primary release, a 0.60 mm strand still fits through the central escape opening. At 6.052 ms the opening traps the yarn. It remains in the pocket through 7.174 ms. All five nose sections contain one fresh, positively oriented crossing during the moving handoff. The 490 sampled poses cover material marks 1055.249–1060.977 mm. The example recomputes the intersections and the escape test from material coordinates and sampled blade outlines. [Moving pickup example](../examples/moving_pickup.py) · [Motion and blade sections](../examples/moving_pickup.npz)

On the separately seated draw, continuing from 1.750 to 2.100 mm raises the secondary gate load to 6.120 mN. The original receiver carries 1.527 mN. Solving the 122 free nodes from the registered geometry gives a maximum remaining force component of 0.0361 nN. The straight withdrawal carries fresh yarn through 3.500 mm in the nominal swept assembly. [Stationary force inputs](../examples/second_draw_210.npz)

```sh
python -m examples.moving_pickup
python -m examples.receiver_load examples/second_draw_210.npz
```

## Routing a compact tool through the held loops

At the seated 2.10 mm draw pose the two openings face different directions. A compact hinged eye follows seven translations around the fork. Its reference point pierces the newly drawn loop on leg three and the previous loop on leg seven. With the loops held in their measured poses, the finite tool clears the installed metal by at least 0.180 mm. Both loop disks in the example follow their own registered material boundaries. [Reproduce the signed crossings](../examples/two_loop_route.py) · [Tool waypoints and registered loop geometry](../examples/two_loop_route.npz)

The stroke also needs enough yarn on the loop side of the eye. The original purchase provides 10.648 mm of relaxed yarn between the eye and the newly drawn loop’s neck. The shortest distance from that neck to the farther disk is 16.005 mm. Sliding the eye farther down the supply strand gives a force-balanced purchase at material mark 1063.645 mm across 18 swept translations. That leaves 20.279 mm of relaxed yarn on the loop side. The two-disk example measures tool passage with the loops held at the seated pose.

```sh
python -m examples.two_loop_route
```

A second eye can also acquire the strand directly at material mark 1064.000 mm with the original cartridge parked. Four translations with 45.013° of combined rotation join this pickup to the six remaining legs of the two-loop route. The connector clears both stationary yarn loops and 726 components by at least 0.05347 mm in the nominal sweep.

In the moving pickup model the second hook bears on fresh material near mark 1056.9 mm. Its first load occurs at 8.274 ms with a 25 µs time-step ceiling and 8.324 ms with a 50 µs ceiling. The corresponding loads of 10.42 and 6.71 mN show the sensitivity of the short contact pulse to time and spatial discretization. The finer run retains the strand through 15.854 ms. A separate moving withdrawal from the same registered 7.174 ms state loads the hook at 0.00483 and 0.00591 mm of travel.

The downstream hook first touches the registered yarn between 0.789398 and 0.789457 mm of travel. At the next stationary calculation, 0.795373 mm, the original cartridge carries 6.108 mN and the new hook carries 0.201 mN. Five sections still contain fresh yarn, and the free-node force imbalance is 0.00114 µN. This is a two-tool equilibrium at the start of the turn.

### Transferring the load to the downstream eye

At 0.795373 mm, a replay of the working strand against 729 component models gives 6.10848 mN on the upstream sliding gate and 0.20088 mN on the downstream hook. Backing the original cartridge toward its entry position unloads its gate. At the same downstream position, with the original gate opened 5.75 mm, the downstream hook carries 3.92686 mN and the fork carries 2.83505 mN. The example reconstructs these reactions from the stored material coordinates, elastic properties, gravity and surface normals. [Force replay](../examples/receiver_load.py) · [First contact state](../examples/downstream_touch.npz) · [Opened source gate](../examples/downstream_released.npz)

In a separate draw with the original cartridge held closed, adding bending degrees of freedom in the working strand resolves the short span between the eye and the guide lip. A 172-free-node stop at 2.995373 mm puts 87.5188 mN on the downstream eye with a 0.530 nN maximum force imbalance. The eye and the guide can bear against different points between two of the original yarn stations. [Refined rod and native bearings](../examples/downstream_fine.npz)

### Metering yarn for the two-loop route

The feeder can donate yarn by lifting the moving pulley and shortening the two spans beside it. The example follows 92 registered points and preserves the original stretch on each supply segment. A candidate draw command transfers 41.2105 mm of relaxed yarn as the supported carrier rises from 154.3051 to 175.5618 mm. This calculation describes the feeder stroke. The two-loop route uses separate checks for the working yarn, both loop crossings, and opening and closing the outlet. [Feeder replay](../examples/draw_feeder.py) · [Wrapped supply and carrier inputs](../examples/draw_feeder.npz)

```sh
python -m examples.receiver_load examples/downstream_touch.npz
python -m examples.receiver_load examples/downstream_released.npz
python -m examples.receiver_load examples/downstream_fine.npz
python -m examples.draw_feeder
```

### Two fresh limbs through both held loops

A constructed endpoint uses one continuous strand from the held fabric to the feeder. In this pose the closed eye surrounds material mark 1076.732 mm. The two limbs intersect the previous loop at marks 1068.869 and 1078.399 mm, and the newly drawn loop at 1053.969 and 1094.157 mm. Each pair crosses in opposite directions around the captured mark. The calculation tracks the material boundaries of the loops and excludes the common neck from the crossing count. [Run the geometric example](../examples/threaded_bight.py) · [Registered strand, loop boundaries and eye pose](../examples/threaded_bight.npz)

This arrangement uses 57.27055 mm of additional relaxed yarn, which the modeled pulley supplies at a carrier height of 183.84612 mm. These numbers describe the specified end shape and feeder setting. The continuous loaded motion into that shape is a separate experiment.

```sh
python -m examples.threaded_bight
python -m examples.draw_feeder 57.270550905
```

### Carrier at the draw station

The XT05 carrier uses a relieved shoe channel and a round-key bore. At the 10 mm draw dock and 20° roll, the nominal fitted shoe has 446.485 mm² of seating area with zero positive overlap. The 30 mm parking dock provides 431.617 mm². The relief removes 519.710 mm³, or 0.247% of the original carrier volume. The STEP file records this candidate in its machine coordinate frame. [Draw-station carrier CAD](../cad/registered_station/XT05_draw_carrier.step)
