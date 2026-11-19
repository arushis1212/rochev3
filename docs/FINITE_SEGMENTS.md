# Contact between two finite yarn segments

The contact patch can end at a yarn-segment tip or lie between nearly parallel pieces. This example integrates one quadratic penalty over both finite material coordinates and returns the force at each of the four endpoints. It accepts oblique, perpendicular and parallel straight segments with positive centerline separation.

Let the two centerlines be x(s) and y(t), where s,t range from 0 to 1. Their rest lengths are L₁ and L₂, diameter is D, and k has units N/mm². Write d = |x(s) − y(t)| and h = max(D − d, 0). The energy is kL₁L₂/(2D) times the integral of h² over the unit square. Differentiating at fixed rest lengths gives the endpoint forces. Each pair contributes equal and opposite forces along its separation vector. Linear interpolation divides the force between the two ends of each segment.

At a fixed s, project x(s) onto the second centerline. If the perpendicular distance is r < D, the active interval extends √((D−r)(D+r)) mm on either side of that projection, clipped to the finite segment. The outer integral is split where contact starts, ends or reaches an endpoint. This catches contact patches much narrower than either segment. Gaussian quadrature controls numerical accuracy within each piece.

The tests check the four endpoint forces against energy derivatives, total force and moment balance, invariance when the segments exchange roles, parallel segments, and the closed-form reference for an oblique interior crossing. Inputs and examples use an illustrative elastic penalty. Yarn compression and hysteresis need measurements on the chosen material. [Interior crossing reference](CONTACT_INTEGRATION.md) · [Calibration for two support directions](SECTION_CALIBRATION.md)

```sh
python -m unittest benchmarks.test_finite_yarn_contact -v
```

[Implementation](../physics/finite_yarn_contact.py) · [Numerical tests](../benchmarks/test_finite_yarn_contact.py)
