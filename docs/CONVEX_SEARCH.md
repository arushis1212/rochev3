# Finite convex search models

The numerical library includes two small optimization methods used to propose
steps in constrained mechanics calculations. Both operate on a local search
model; acceptance still requires the caller's original energy, force and
geometric constraints.

`boxed_spd_direction(H, g, h)` minimizes

`gᵀd + ½ dᵀH d`, subject to `|d_i| ≤ h`,

for one or two coordinates and positive-definite `H`. It enumerates the
feasible unconstrained minimum and the clipped minimum on every face. This
finds the box-constrained minimum even when uniformly scaling an unconstrained
Newton step would over-reduce a stiff coordinate.

`quadratic_direction(A, g, gap, J, K, solver="dual_nnls")` uses a positive
inverse search metric `A` and affine normal-gap rows `gap + Jd`. It minimizes

`gᵀd + ½ dᵀA⁻¹d + ½ Σ K_i min(gap_i + J_i d, 0)²`.

With `U = diag(sqrt(K)) J` and `d₀ = −Ag`, the equivalent nonnegative dual has
`Q = I + UAUᵀ`, `b = sqrt(K) gap + Ud₀`, and reconstruction
`d = d₀ + AUᵀp`. A Cholesky factor converts the dual to nonnegative least
squares. Finite iteration limits, complementarity checks, finite arithmetic
and descent checks govern the proposed result.

The selected gap rows model possible contact during the search. They do not
replace the complete physical contact evaluation. The search metric need not
be the physical Hessian, and a successful quadratic solve does not establish
equilibrium of the full machine.

Seven benchmarks compare against analytical solutions, exhaustive five-row
active-set enumeration and boundary optimality conditions:

```sh
python -m pip install -r requirements-fea.txt
python -m unittest benchmarks.test_convex_search -v
```
