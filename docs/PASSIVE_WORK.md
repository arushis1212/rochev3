# Can a passive guide supply the work its command requires?

A moving guide can add energy to a strand or extract energy from it. At every point the initial kinetic energy plus cumulative external work, less the change in stored potential, must cover kinetic energy and accumulated dissipation. A negative balance identifies an impossible passive command under the stated assumptions.

| Command end | External work increment, mJ | Potential change from start, mJ | Available energy from rest, mJ |
| --- | ---: | ---: | ---: |
| 1 | +4 | +3 | +1 |
| 2 | −5 | +1 | −2 |
| 3 | +1 | 0 | 0 |

This example requires at least **2 mJ** of extra initial energy to pass the energy test at command 2. The final command returns the balance to zero. Each work increment is added once. Each stored-energy value is referenced to the start. Rational intervals propagate uncertainties on both quantities and give lower and sufficient bounds on the additional energy.

For the example, cumulative work and potential are affine within each command, so checking the two ends covers its interior. For a measured or simulated nonlinear path, supply independent interior bounds or subdivide and bound the variation between samples. Passing this necessary energy test still leaves contact forces, momentum, dissipation and the actual trajectory to determine.

Run the example and six regression cases from the repository root.

```sh
python3 examples/passive_work.py
python3 -m unittest benchmarks.test_passive_work
```

[Example source](../examples/passive_work.py) · [Repeatable checks](../benchmarks/test_passive_work.py)
