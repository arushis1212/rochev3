# Continuous aperture geometry

The aperture is an oriented triangle disk whose vertices follow fixed yarn
material coordinates. The checker covers an affine interval of inspected yarn
motion using projected triangle orientation, a simple projected boundary and
finite separation from the physical boundary and virtual closing chord.

Projected signed triangle areas are quadratic in time. Their interval minima
include stationary points. Cross and dot calculations carry reserves based on
product magnitudes before cancellation and coordinate formation. Each accepted
time interval uses a fixed projection with positive triangle orientation and
a bijective boundary; these conditions imply an embedded disk under the
[global simplicial inversion theorem](https://arxiv.org/abs/1310.0955).

For moving segment pairs, the maximum relative endpoint speed bounds the
change in distance. Subtracting that speed times the half-interval from the
midpoint distance gives the continuous separation bound. Common translation
cancels. Point and short segments retain finite distance bounds and remain
included in the query. Adaptive subdivision and a finite selection of
projections preserve the same material path and triangulation.

Results include input hashes, thresholds, accepted interval bounds and the
scope of the geometric certificate. Force equilibrium, physical retention
and material passage events have separate checks. The module uses numerical
arithmetic with explicit reserves.
