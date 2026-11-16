# Mechanism and mathematics

The initial hardware is a manually actuated research fixture. Its purpose is to
study loop registration and stitch mechanics using printable structural pieces,
metal yarn-contact tooling and purchased fasteners/bearings.

GlobalX spans the stitch stations, Y points toward the rear and Z points upward.
The hook's localu axis points toward its tip. The JSON defines dimensions, motion
coordinates and manufacturing admission values; the Python constructs the solids.

| Subsystem | Design |
|---|---|
| Hook | Machined strip body, sliding closure, supported rotating barrel |
| Registration | Four paired-support stations on24mm pitch |
| Positioning | Manual XYZ stages for hook and guide; separate hook roll |
| Guide | Stepped brass tubes and bonded reducing bushes |
| Feeder | Moving pulley, central cord attachment, two counterweight idlers |
| Fabric handling | Hanging clamp and an open passage through the base |

The feeder uses T≈mg/2 for a symmetric, frictionless moving pulley. The target
moving mass is12.848g; its model explicitly counts polymer parts, bearing,
fasteners, brass spacers and a cord/adhesive allocation. A counterweight changes
the ideal balance toT≈(m−mc)g/2. Real assembly mass and friction are measured
quantities; density ceilings and allowances in the inputs are design admissions.

For each countercord leg, h is the vertical drop from the idler center, a is the
horizontal center offset, and R includes half the cord diameter. The straight
length is√(h²+a²−R²), and the wrap contribution is
R[π/2+atan2(h,a)−acos(R/√(h²+a²))]. Adding both legs and the32mm top span gives
214.706745509mm effective length at the midstroke geometry. CAD solves this same
constant-length constraint for the counterweight position. The254mm rough cut
includes knot and trimming allowance.

These equations define a quasistatic, inextensible, frictionless reference case.
They are useful design calculations rather than measured textile behavior.
The first hardware scope is single-stitch/swatch research; dimensional data here
is prototype geometry, not an automatic garment-production program.

The local strand module uses elastic stretch energy EA(l−l0)²/(2l0) and
isotropic discrete bending energy2B(1−cosθ)/(lbar(1+cosθ)). Contact uses
finite yarn radius and a reference-length-weighted penalty against the pocket
cross-section. Its scope is planar quasistatic mechanics with prescribed ends;
friction, twist,3D loop connectivity and material calibration are separate
modeling stages. Numerical examples use explicit benchmark parameters.

## Nominal geometry checks

The current design was checked at69 rigid assembly states, including selected
reverse-row poses: zero solid overlaps and zero joint-limit violations. A
bounding-radius calculation gives2.2712mm separation between the rotating tool
and the Z rail throughout a complete roll. These are nominal rigid-geometry
results. See [numerical record](GEOMETRY_CHECKS.json) for the evaluated states.
