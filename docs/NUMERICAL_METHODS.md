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

Yarn gravity is available as a reference-length mass term. Each edge contributes half its weight to each endpoint; total nodal weight equals the prescribed linear mass times total reference length and gravity. A source reference of1786dtex corresponds to0.1786g/m. The source cotton mass and the declared synthetic stiffness parameters remain distinct inputs. Analytic tests check total force, energy translation and gradients.

Contact-scale differentiation is checked against an analytic near-onset penalty benchmark. The loaded component endpoint converges with contact spacings0.05,0.025 and0.0125mm. Successive node-position changes are0.02190 and0.00890mm. Segment/AABB slab intervals preserve the exact original midpoint indices and weights; they change evaluation cost rather than quadrature or physical geometry.

A T15 fixed-geometry contact-penalty sensitivity study at advance−1.6mm uses2000/4000/8000N/mm². The finite-radius gap lower bounds are−0.0085771/−0.0064988/−0.0050387mm. This tests numerical hard-obstacle compliance;8000 is the whole-feed study coefficient, separate from real yarn compression. Mesh convergence and physical constitutive calibration are separate qualifications.

[Whole-material mesh sensitivity](FEED_MESH_STUDY.json) partitions95 nodes into189 at a fixed commanded pose, preserving material length, cloth attachments and nip. The energy, material-position, clamp and feeder changes are recorded alongside endpoint forces and geometry. Uniform axial-strain energy and endpoint forces are analytically invariant under subdivision; the tests check this independently.

An optional absolute-Hessian search metric uses the reciprocal of max(abs(eigenvalue), epsilon). Its direction has negative dot product with the energy gradient; a line search still evaluates the unchanged physical energy. This preserves curvature scales when the Hessian is indefinite. Known-minimum nonconvex tests verify the search behavior.
