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
