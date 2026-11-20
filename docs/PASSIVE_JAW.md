# A spring shoe for the fabric clamp

A pin on the hanging fabric clamp carries the yarn around a turn. Beside the pin, a small shoe presses on the yarn. Two thin stainless leaves support the shoe. As the yarn diameter changes, the shoe moves and continues to exert a normal force. This component study uses a 0.55–0.60 mm strand.

| Dimension | Prototype value |
|---|---:|
| Free span of each 301 stainless leaf | 14.00 mm |
| Width × nominal thickness | 0.65 × 0.050 mm |
| Distance between leaf center planes | 1.00 mm |
| Angle of the leaves in the clamp’s XZ plane | 6° |
| Calculated unloaded shoe setting relative to the original jaw face | 0.316215 mm |

The angle routes the spring pocket around an existing M3 fastener. In the installed CAD, the pocket clears the fastener by 0.964 mm. The deep spring recess clears the pin by 0.400 mm and the shoe clears it by 0.160 mm.

## What to measure on a coupon

The predicted forces below are for the same yarn centerline and the same setting of the jaw. The model integrates contact over the finite shoe face and allows both leaves to extend and bend. The supported shoe can also rotate. The numbers give a target for testing the assembly.

| Yarn diameter | Shoe normal force | With a ±0.050 mm error in the unloaded setting |
|---|---:|---:|
| 0.600 mm | 3.442 mN | 2.901–3.982 mN |
| 0.575 mm | 3.307 mN | 2.765–3.847 mN |
| 0.550 mm | 3.172 mN | 2.630–3.712 mN |

Cut and clamp two strips with the specified free span. Measure their actual thickness, the free shoe position, and the force–displacement curve on loading and unloading. Include 2.5, 3.5 and 4.5 mN and record the return position after each cycle. Allow longitudinal motion at the tip. The largest modeled retreat was 0.0126 mm in the three load and stock cases studied. Check for contact with the shaft and measure how much force actually reaches the shoe.

For a rectangular beam, bending stiffness scales with the cube of the strip thickness. The model uses a Young’s modulus of 185 GPa. The largest calculated unnotched outer-fiber stress in the three cases was 73.25 MPa. The edge condition and the clamp at the root matter when testing actual spring life. [NASA Langley beam analysis](https://ntrs.nasa.gov/api/citations/20200002944/downloads/20200002944.pdf) · [301 stainless strip material data](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXUK/assets.files/material-data-sheets/stainless-steel/stainless-steel-1.4310-301.pdf)

## Load carried by the floating cloth clamp

At one swatch-holding pose, the 23.94 g clamp settles against two existing pins and its passive shoe. The calculation releases all three translations and three rotations. Three bonded yarn nodes move with the clamp. The other material coordinates stay at their recorded shape. An independent integration of 957 yarn segments against 23 native clamp bodies checks the forces and moments.

| Yarn diameter | Net force and moment error, expressed as force | Upward reaction at return pin | Upward reaction at right pin | Smallest restoring stiffness |
|---|---:|---:|---:|---:|
| 0.575 mm | 0.0000384 mN | 84.55 mN | 116.74 mN | 0.427 N/mm |
| 0.550 mm | 0.0000098 mN | 64.19 mN | 117.15 mN | 0.518 N/mm |

For each row, compare the largest absolute component of net force with the Euclidean norm of the net moment divided by the 44 mm reference length. The table reports the larger value. The two cases retain at least 0.007689 and 0.005953 mm, respectively, inside the modeled 0.010 mm compression limit throughout their approach. [Force vectors, moment vectors and reference length](../examples/floating_clamp_result.json)

The next calculation releases ten yarn nodes at the two pin wraps along with the clamp, giving 36 free coordinates at the same pose. The independently integrated residual on the yarn is 1.77 nN at 0.575 mm and 2.02 nN at 0.550 mm. For the narrower yarn, pressure also reaches the finite end of the spring shoe. The lowest restoring stiffness is 0.4384 and 0.5231 N/mm respectively in the scaled coordinate system. Both modeled passages stay open throughout the approach. The material outside the released neighborhoods retains its recorded shape.
