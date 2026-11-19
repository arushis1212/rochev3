# A passive carrier supported by yarn

Two symmetric compliant contacts support a circular carrier under gravity. Moving the contacts apart changes the equilibrium height even when the load stays constant. This analytical example isolates that relationship and checks the restoring stiffness.

Let each fixed contact lie a horizontal distance *x* from the vertical centerline. The carrier rises a distance *h* above the contact plane. The radial distance is ρ = √(x² + h²). Each contact compresses by δ = max(0, a − ρ), with free contact radius *a* and stiffness *k*. The two contacts supply an upward force 2kδh/ρ. The equilibrium condition sets that force equal to *mg*.

On the loaded branch, the derivative of the vertical potential gradient is 2k(1 − ax²/ρ³). The example brackets the stable root between the point of zero stiffness and the height where the contacts release. Positive stiffness within that interval gives a restoring force after a small displacement. The model describes frictionless, quasi-static normal contact.

Run both the example and its analytical checks from the repository root.

```sh
python -m examples.gravity_carrier
python -m unittest benchmarks.test_gravity_carrier
```

One test uses a 6–8–10 triangle and two 0.5 mm compressions at 1 N/mm. The two vertical components together support exactly 0.8 N at an 8 mm height. Other tests compare the derivative to a centered finite difference and exercise unloaded and overloaded cases.

The same example bounds a range of applied forces. For any constant vertical load between 0.7 and 0.9 N, the stable height lies between 7.91913 and 8.07993 mm. The force derivative is positive and increases with height on this branch. The heavier endpoint therefore sets both the lowest height and the least restoring stiffness, 1.22916 N/mm. These bounds assume a steady applied load and frictionless normal contact.

[Executable model](../examples/gravity_carrier.py) · [Analytical checks](../benchmarks/test_gravity_carrier.py)

## Interpolation around a fixed wheel

A straight line between two perfectly seated yarn positions can cut into the wheel. For centerline radius *R* and endpoint angle θ, the chord midpoint lies at radius *R* cos(θ/2). The greatest radial clearance loss is 2*R* sin²(θ/4). This exact bound applies over the entire minor arc of a rigid circular section. A constant axial advance along a helix leaves the radial calculation unchanged.

For a 12 mm radius and a 60° turn, one chord cuts inward 1.607695 mm. Eight equal chords reduce this to 0.025693 mm. Ten are needed for a 0.020 mm radial allowance. A normal contact spring of stiffness *k* would add a force *k* times this spurious penetration while contact remains active. The centerline geometry alone gives no value for *k*.

Run `python -m examples.wheel_wrap` for the interval table and `python -m unittest benchmarks.test_wheel_wrap` for the analytical and boundary checks. [Circular interpolation calculation](../examples/wheel_wrap.py) · [Tests](../benchmarks/test_wheel_wrap.py)
