# Unilateral contact with friction

The contact example solves a finite, small-displacement elastic model with opening, sticking and sliding. It keeps the normal nonpenetration condition separate from tangential friction. Sliding therefore does not introduce an artificial normal opening requirement.

The input operator `B` maps elastic displacements to area-average contact gaps in millimetres. Its transpose maps contact resultants in newtons back to nodal forces. Compression-positive normal resultants satisfy

`K u = f + Bᵀλ`, `g = B u + g₀`,

`gₙ ≥ 0`, `λₙ ≥ 0`, `λₙ gₙ = 0`.

For a fixed normal-force bound, the tangent law opposes incremental slip with a norm bound `μ p_old`. An ADMM iteration alternates an augmented elastic solve with normal projection and radial tangent shrinkage. A separate outer iteration updates the normal bound and checks the final Coulomb law against the actual normal resultant. The numerical augmentation contributes no physical stiffness to the final equilibrium equation.

The caller supplies the elastic linear solve, residual tolerances and finite iteration/deadline limits. The method reports incomplete convergence explicitly. For load histories, `g₀` preserves the previous accepted tangential displacement; it does not reset accumulated motion to an undeformed reference.

The convex inner splitting follows [Boyd et al.](https://web.stanford.edu/~boyd/papers/pdf/admm_distr_stats.pdf). [GetFEM's contact documentation](https://getfem.org/userdoc/model_contact_friction.html) gives the underlying normal and friction conditions and the small-sliding approximation. The outer Coulomb iteration needs its own convergence check. Averages over a contact patch do not establish pointwise contact laws; applying the example to physical geometry also requires pointwise checks, material data and spatial refinement.

Run the analytical opening, sticking, sliding, reversal and force-unit benchmarks:

```sh
python -m pip install -r requirements-fea.txt
python -m unittest benchmarks.test_unilateral_contact -v
```

The implementation is in `physics/unilateral_contact.py`.
