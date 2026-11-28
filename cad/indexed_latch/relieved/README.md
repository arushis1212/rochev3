# Relieved fork and folding tooth

A machined flat lets the indexed support withdraw through two retained yarn loops. The proximal rail land carries the yarn during pickup. A stepped collar supports the two sleeve bearings while the tooth folds into the withdrawal position.

The finished fork and rotor STEP files use the same world coordinates as the indexed-latch example. The shallow fork and deep removal STEP files represent the bounding machining conditions. The shallow envelope uses the original remote tail. The finished fork contains its rebalanced tail.

| Dimension | Value |
| --- | --- |
| Rail flat angle and offset | 40° ± 0.30°, 0.600 ± 0.006 mm |
| Proximal and distal limits along the slide axis | −2.120 ± 0.010 mm to +4.150 mm |
| Journal support radii | 0.355 mm through the inner 0.590 mm on each side, then 0.295 mm |
| Deployed tooth diameter | 1.000 mm |
| Withdrawing stroke | 29.701763 mm |
| Worst-case clearance in the modeled machining window | 0.040954 mm |

The shallowest cut leaves the most metal on the withdrawal path. The sweep checks the entire 0.600 mm diameter registered yarn against that material over the full stroke. A combined 0.035 mm allowance for relative component pose, yarn path, radius growth and displacement leaves 0.005954 mm. These values specify an inspection budget for the modeled withdrawal.

Three registered yarn edges show where the earlier advancing strand bears on the upstream rail. The native tests check contact on the finished fork and positive separation from the deepest removal envelope. They also reconstruct the mass and centroid of the installed assembly and test the seated index in both rotational directions.

Run the benchmark from the repository root with NumPy and CadQuery installed.

```bash
python -m unittest -v benchmarks.test_latch_clearance
```
