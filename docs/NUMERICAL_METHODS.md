# Efficient coupled yarn and clamp equilibrium

The rod interior has a banded Hessian; five clamp coordinates form a small
border. Block elimination solves the clamp Schur complement and then recovers
the rod direction. Numerical damping changes only the search direction, while
force residuals are checked against the original physical potential. Active
nonlocal contacts trigger a full-Hessian fallback.

A segment-pair broad phase uses enclosing-box distance lower bounds and one
exact distance upper bound. Keeping every pair below the larger of that upper
bound and the yarn diameter preserves all active penalties and the exact minimum
separation. Exhaustive-pair tests verify energies, gradients and distances.

Adaptive temporal subdivision bounds linear interpolation between two material-
matched shapes. Distance to a solid is1-Lipschitz; half a time-cell's maximum
motion bounds its unobserved distance loss. The two-strand bound uses twice the
single-strand motion. These are centerline topology certificates for the stated
interpolation, alongside separate finite-radius contact and equilibrium checks.

The tests include a dense linear-algebra oracle, exhaustive contact evaluation,
analytic gradients and deliberately crossing interpolation paths. Run the full
suite with the README's command.

A [nested endpoint experiment](ENDPOINT_REFINEMENT.json) records33 through2049 material nodes. The final refinement changes rod energy by0.133%, clamp position by0.01025mm and material-point position by0.06370mm. These quantities describe one synthetic, quasistatic castoff endpoint on the T6 reference geometry.

Exact line/arc distance evaluation also has a compiled numerical implementation. Random points, profile vertices and independent reference calculations check equivalence; no fast-math transformations are enabled. Adaptive moving-solid subdivision uses the same Lipschitz bounds with smaller temporal cells.
