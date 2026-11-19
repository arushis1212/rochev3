# Newton method for fixed-friction contact

This small analytical example solves contact equilibrium by applying Newton steps to a projection residual. It handles opening, sticking and sliding in the same system. The friction radius stays fixed during a solve, so this is a Tresca subproblem.

With displacement `u`, contact resultant `λ`, relative gap `g = Bu + g₀` and a positive numerical scale `ρ`, the equations are

```
Ku − f − Bᵀλ = 0
λ − Project_D(λ − ρg) = 0
```

`D` is the product of a nonnegative normal-force half-line and a tangential disk of radius `μ p_old`. Normal complementarity stays separate from the sliding law. The numerical scale changes the solution procedure, while the final force balance uses the original stiffness `K`.

The implementation derives the exact generalized Jacobian in scaled coordinates, checks each linear solve and accepts a step only when the complete force/contact residual merit decreases. It retains explicit iteration limits. The dense example rejects singular Jacobians; this is a conservative numerical decision, not a conclusion that a physical contact problem has no solution.

The benchmarks cover mixed contact states with known coupled solutions, directional derivatives, a sliding case with zero normal opening, switching boundaries, restart equivalence and redundant constraints. They run independently of the machine CAD:

```sh
python -m pip install -r requirements-fea.txt
python -m unittest benchmarks.test_semismooth_contact -v
```

See [`physics/semismooth_contact.py`](../physics/semismooth_contact.py) and the complementary [ADMM example](UNILATERAL_CONTACT.md). A Coulomb application additionally needs an outer normal-force update, accepted displacement history and geometry/material validation.

[GetFEM's official contact documentation](https://getfem.org/userdoc/model_contact_friction.html) presents projection formulations and their small-sliding context. [Kunisch and Stadler (2005)](https://www.numdam.org/item/10.1051/m2an:2005036.pdf) develops generalized Newton methods for Tresca contact and a separate fixed-point approach to Coulomb friction. These references support the numerical approach; the examples demonstrate their stated finite-dimensional cases.
