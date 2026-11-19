# How much yarn must the guide receive?

A retracting guide can demand more yarn even when two surrounding points stay still. Roche’s worked example moves the guide 32.356 mm along its axis. The original material span is 278.865 mm. At the end of the stroke any continuously threaded span between the two fixed points needs at least **283.693 mm**, a **4.828 mm** difference. A moving feeder, movement of the bounding material points, or elastic extension can supply that difference.

The guide opening is a disk. For an endpoint at perpendicular distance `z` from the disk plane, at in-plane radial distance `r` from its center, and bore radius `R`, its closest distance to the disk is `hypot(z, max(0, r − R))`. Sum that distance for both endpoints. This permits each endpoint to choose its own nearest disk point, giving a lower bound for any strand crossing the opening. Translating the disk by at most `δ` can lower the sum by at most `2δ`. The direct distance between the endpoints supplies a second lower bound. The example takes the larger of the two. The full bore treats the yarn centerline favorably. Contact friction and bending enter the subsequent force calculation.

Run the calculation or change the coordinates in the input file. Both the example and its tests use the Python standard library. [Inputs](../examples/guide_travel.json) · [Calculation](../examples/guide_length.py)

```sh
python3 examples/guide_length.py
python3 -m unittest benchmarks.test_guide_length
```
