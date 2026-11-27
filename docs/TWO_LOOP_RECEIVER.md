# Receiving two yarn loops

After the first draw and guide parking, the previous loop sits in the heel of the main hook and the newly drawn loop sits in its nose. Their openings face different directions. An inclined receiver can enter both while the main hook stays closed and the supply outlet holds the same registered length of yarn.

The probe example uses a 1.50 mm diameter needle and a 0.60 mm nominal yarn diameter. Over the finite approach, the needle surface clears the yarn by 0.951 mm and the nearest installed hardware by 1.527 mm. The example recomputes the yarn distance from the stored polylines. The hardware number uses the axis-to-solid distance measured in the fitted assembly.

The closing receiver pairs that needle with a 2.10 mm diameter return finger. The fingers are 10 mm apart. After 29.702 mm of insertion, a transverse pin closes the opening. The nominal sweep includes the bridge, return finger, gate boss and pin. Its smallest modeled clearance is 0.810 mm to the yarn and 1.470 mm to hardware.

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
