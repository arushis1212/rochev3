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

[Executable model](../examples/gravity_carrier.py) · [Analytical checks](../benchmarks/test_gravity_carrier.py)
