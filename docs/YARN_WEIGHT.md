# How yarn weight changes a common equilibrium

Consider a strand with segments of 10, 20 and 30 mm, held at the same coordinates with two different linear densities, 100 and 160 tex. The second internal node supports half of the 20 mm and 30 mm segments. Its 25 mm share acquires an extra 14.709975 µN of weight. If all remaining forces at this position stay the same in both calculations, then at least one of the two has a vertical force imbalance of 7.3549875 µN or more. Changing the restraints, constitutive law or pose changes the question.

For density difference Δρ in tex and a node’s share of rest length L in millimetres, the magnitude of the change in weight is 9.80665 × 10⁻⁹ |Δρ| L newtons. Interior nodes have half the lengths of both adjacent segments. An end node has half of its single segment. At a free node the two residuals differ by exactly this weight change, so their maximum absolute value is at least half its magnitude. A fixed support can supply different reactions at each density.

Run `python3 examples/yarn_weight.py` from the repository root. The benchmark compares every node with the rod assembly’s gravitational forces and checks its potential energy and total weight. [Example](../examples/yarn_weight.py) · [Tests](../benchmarks/test_yarn_weight.py)
