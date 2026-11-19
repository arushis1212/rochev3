# A screw beside a moving yarn path

A small head leaves more room for yarn. A wider flat underside spreads the clamp load across the pad. This example calculates the diameter interval that satisfies both conditions for a cylindrical head with a planar bearing face.

In the example, the yarn centerline stays 2.50 mm from the screw axis while the yarn overlaps the head axially. Yarn radius, positioning allowance and required free gap consume 0.35, 0.25 and 0.10 mm respectively. The head may use at most the remaining 1.80 mm of radius, so its outside diameter must be at most 3.60 mm.

For a 24 N joint load and 25 MPa allowable average bearing pressure, effective contact area must reach 0.96 mm². If a measured imprint covers 80% of the available annulus, the geometric area must reach 1.20 mm². Starting at an inner land radius of 1.20 mm gives a required outer land radius of about 1.35 mm. With a 0.10 mm unsupported rim, the minimum head diameter is about 2.90 mm. The support must also extend to that required land radius.

The inputs are an independent numerical example. A physical application needs measured head and hole dimensions, pad-edge distance, retained preload, imprint fraction and allowable pressure for the selected surfaces. Axial clearance, joint slip, edge stress, threads and wear have separate acceptance conditions. Run `python3 examples/retaining_screw.py` to reproduce the interval. [Calculation](../examples/retaining_screw.py) · [Analytical benchmarks](../benchmarks/test_retaining_screw.py)
