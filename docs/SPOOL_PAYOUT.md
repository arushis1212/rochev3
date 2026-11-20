# Seven turns between two marks on one strand

In the modeled manual threading route, a shuttle takes the working end of a single strand through the upper opening of a foundation loop and returns through its lower opening. Two marks on that strand fix how much material the shuttle must deliver between passes. Their separation is **140.571683 mm**. The example sizes one cylindrical winding layer and a sliding takeoff for this interval.

| Quantity | Nominal value |
| --- | ---: |
| Material marks measured from the start of the strand | 219.308769 and 359.880452 mm |
| Spindle rotation | 7 turns |
| Axial takeoff advance | 0.840 mm per turn |
| Helical material unwound | 146.451683 mm |
| Increase in the straight length inside the shuttle | 5.880000 mm |
| Material delivered through the eye | **140.571683 mm** |

For centerline radius (R) and axial pitch (p), one turn unwinds `hypot(2πR, p)` mm. The takeoff advances one pitch along the same axis, lengthening the straight internal segment by (p). For required delivery (d) per turn, solving these two length relations gives `R = sqrt(d × (d + 2p)) / (2π)`. The example also evaluates the forward relation and checks the helix against a 4,096-chord reconstruction.

The calculation assumes an unstrained strand, constant winding radius and pitch, and tangency at the takeoff. The winding radius measures to the centerline of the yarn. The calculation gives a nominal geometric payout; friction, deformation and physical delivery depend on the wound assembly.

```sh
python3 examples/spool_payout.py
python3 -m unittest benchmarks.test_spool_payout
```

[Design calculation](../examples/spool_payout.py) · [Reproducible checks](../benchmarks/test_spool_payout.py)
