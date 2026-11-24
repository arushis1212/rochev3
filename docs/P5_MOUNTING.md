# Hook, stripper and spring mounting assembly

This CAD reference places the steel hook, brass gate, stripper mechanism, three spring sockets and station supports in one machine coordinate system with the head parked. The assembly contains 221 named members. Decompress the STEP and open it in a STEP assembly reader. The parts table gives the individual labels, centroids and material volumes in machine coordinates. [Assembly STEP, gzip](../cad/p5_fitting/P5_fit.step.gz) · [221 named members](../cad/p5_fitting/parts.csv)

| Mounting interface | Dimension in this assembly |
| --- | --- |
| Printed cover origin in machine XYZ | (94, 165.5, 68) mm, axes parallel to the machine axes |
| New retaining leaves | 9.30 × 1.00 × 0.10 mm |
| Leaf insertion | 2.90 mm stroke, 0.030 mm minimum geometric clearance |
| Cover to bed | Five front M2 × 16 and five rear M2 × 24 screws. The rear screws also pass through the metal bridge. |
| Base board to receiver | Four Ø4.50 mm through-holes for M4 × 20 bolts, 0.25 mm nominal radial clearance |
| Gate reference | One 0.0508 mm steel foil and a 4.500 mm strip |

The cover incorporates the three spring sockets in one solid. Its detached part uses the cover datum above. The drilled board is supplied in machine coordinates. At the specified assembly pose, the nearest unloaded retaining leaf is 0.11994 mm from the hook. The loaded station position is gauged after tightening the bolts. [Three-socket cover STEP](../cad/p5_fitting/B02_three_root_cover.step) · [Drilled base STEP](../cad/p5_fitting/F03_receiver_drilling.step) · [Gate setting and geometry](CAPTURE_GATE.md)
