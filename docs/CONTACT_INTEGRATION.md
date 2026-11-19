# Contact integration benchmark

Two straight rods crossing at right angles provide a closed-form reference for
contact energy and force. The example compares segment-pair quadrature with
that reference at progressively finer spacing.

For diameter `d`, positive centerline separation `h < d`, penalty coefficient
`k` and `a = d−h`, the distributed quadratic penalty is

```text
E = k/(2d) ∫∫ max(d − sqrt(x²+y²+h²), 0)² dx dy
  = πk [a³/3 − a⁴/(4d)]

F = −∂E/∂h = πkh a²/d
```

The rods extend beyond the active disk of radius `sqrt(d²−h²)`. Units are mm,
N and N/mm². This benchmark uses prescribed elastic contact properties and
straight geometry; measured yarn behavior is a separate model input.

At `d=.6`, `h=.59998` and `k=1000`, the exact force is
`1.256595174e−6 N`. The segment-pair rule evaluates each pair at its closest
point and applies the resulting penalty over its parameter cell.

| Segment spacing, mm | Active pairs | Numerical / exact force |
|---:|---:|---:|
| .001 | 88 | 1.370511 |
| .0005 | 332 | 1.180403 |
| .0001 | 7,716 | 1.034905 |
| .00005 | 30,520 | 1.017391 |

Distance bounds cull inactive pairs exactly. A finite pair budget bounds the
example's computation. Tests independently check the energy derivative,
convergence toward the integral, separated rods and input limits.

```sh
python examples/crossed_rods.py
python -m unittest benchmarks.test_crossed_rod_contact -v
```
