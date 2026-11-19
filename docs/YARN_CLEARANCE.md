# Continuous yarn self-clearance

The example opens a two-turn helix from a pitch of 1.2 mm to 2.2 mm at a fixed 6 mm radius. The code constructs 129 material points directly from the helix equation. Each segment carries a 0.30 mm yarn radius. The example tests the calculation on a known shape.

```sh
python -m examples.yarn_sweep
python -m unittest benchmarks.test_yarn_sweep
```

The material registry compares segments with intervening rest length greater than π times the yarn radius. Each segment moves linearly between poses. A box containing its four endpoint positions encloses the entire sweep. If two box bounds approach the clearance threshold, the code tests their segments directly.

Projecting both segments onto a unit direction gives a lower bound on their distance. Over a fraction *h* of a step, the distance can fall by at most *hV*/2 from its midpoint, where *V* is the maximum relative displacement between endpoints of the two segments over the full step. Convex interpolation makes the bound valid anywhere along both segments. The calculation subtracts the yarn diameter and a 0.00000001 mm numerical reserve, then subdivides any interval where its lower bound needs refinement.

All 63,000 pair-intervals of the analytical example have a conservative signed surface separation of at least 0.43554 mm. The tests also include a crossing halfway between two clear endpoint poses and a pair that moves together under translation.

[Executable example](../examples/yarn_sweep.py) · [Regression cases](../benchmarks/test_yarn_sweep.py)
