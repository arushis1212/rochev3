# Material length, contact integration and motion

The numerical toolkit integrates contact over reference yarn length. Each edge
uses n=max(32,ceil(L0/h)) midpoint samples, with weight L0/n. Sample counts stay
fixed during a solve, preserving the analytic energy derivative. A conservative
expanded solid bounding box skips only points with zero contact penalty; active
points retain the exact line/circular-arc distance calculation.

The free-clamp formulation lets fabric attachments translate and rotate while
six tension-only neighboring members and gravity provide a load path. Elastic
strain is therefore evaluated alongside geometric length redistribution. Material
EA, bending rigidity and the textile-member law remain declared model inputs.

For linearly interpolated strand positions, let M be the largest vertex movement
and R the largest rigid-solid translation. If endpoint centerline-distance lower
bounds are d0,d1, then min(d0,d1)-(M+R)/2 is a conservative lower bound over the
transition. A positive value protects centerline noncrossing. Finite yarn radius,
material data and the full installed contact geometry require their own checks.

The local T14 CAD includes the lift carriage, matched guide axes, anchor screws
and nuts. Its guide-axis location is5.7256mm and nominal carriage/plate separation
is0.30mm. Part files form a separate mechanism study alongside the D22 fixture.

Run the analytic regressions with:

```sh
.venv/bin/python -m unittest tests.test_transfer_numerics -v
```

The long-edge contact test compares numerical integration against an exact plane
integral. Other tests check independent CAD distances, force gradients, search
metric admissibility and rejection of a crossing transition.
