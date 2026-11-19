# Bounded quadratic search

The mechanics library provides two independently checked solvers for

`minimize gᵀd + ½dᵀHd, subject to −h ≤ dᵢ ≤ h`, with symmetric positive-definite `H`.

`physics.boxed_quadratic.minimize_spd_box` enumerates all active faces for up to seven coordinates. Each face fixes its boundary coordinates and solves the remaining linear system. Comparing every feasible face minimum gives the global solution of this small convex problem.

`physics.bounded_dense_quadratic.minimize_spd_box_bvls` handles up to nineteen coordinates. If `H = LLᵀ`, its equivalent bounded least-squares problem is

`minimize ½‖Lᵀd + L⁻¹g‖²`.

The omitted term is constant in `d`. The implementation verifies finite arithmetic, coordinate bounds and the original quadratic's optimality conditions: zero gradient at free coordinates, nonnegative gradient at lower bounds, and nonpositive gradient at upper bounds. Its result includes the condition number, iteration count and optimality residual.

Tests compare both methods on sixteen small random problems and use three dense nineteen-coordinate problems with analytically prescribed active constraints. They also check input immutability and invalid-result rejection.

```sh
python -m pip install -r requirements-fea.txt
python -m unittest benchmarks.test_bounded_dense_quadratic -v
```

These methods produce steps for a local numerical search model. The surrounding mechanics solver evaluates the original material/contact equations and geometric constraints before accepting a step.
