# Guide bracket mounting ring

A machined brass ring sits under each M2 screw that holds the guide’s indexing bracket to the spine. The ring spreads the load into a pocket in the printed foot. Two rings seat each bracket.

| Feature | Dimension |
|---|---|
| Outer diameter | 4.18–4.20 mm |
| Through-bore | 3.100 ± 0.025 mm |
| Thickness | 0.79–0.81 mm |
| Material | C260 brass |
| Reference screw | Bossard BN 612 M2 × 8, article 1233696 |

The STEP solid has its axis along X and its floor datum at X = 0. It uses millimetres. [Bracket ring STEP](../cad/bracket_ring/bracket_ring.step) · [Dimensions, volume and file hash](../cad/bracket_ring/geometry.json)

The screw catalog gives a minimum 3.48 mm diameter for its flat bearing face. With the ring centered within 0.150 mm of the screw and a maximum screw tilt of 0.005 rad, the minimum projected bearing face extends 0.0275 mm beyond the bore around its full circumference. The neck retains at least 0.0849 mm radial clearance. Those geometric margins apply to inspected parts. [Manufacturer’s dimensions](https://bossard.partcommunity.com/3d-cad-models/?countryIso=US&info=bossard%2F01%2F01_100%2F01_100_100%2F01_100_100_10%2Fbn_610_612_31101%2Fbn_612.prj&languageIso=en) · [Bracket load model](PLANAR_JOINT.md)

In assembly the offset budget allows 0.070 mm ring movement in the pocket, 0.030 mm pocket location error, 0.040 mm screw location error and 0.010 mm bore eccentricity. The six modeled seats each provide at least 5.185 mm² of backing on the nominal foot geometry. The physical receiving test measures the bearing imprint and retained bolt force after dwell under reversing wheel load. [Backing-area method](WASHER_SUPPORT.md)
