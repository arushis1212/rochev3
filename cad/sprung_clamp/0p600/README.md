# Sprung outlet for 0.600 mm yarn

The cup and retainer locate a spring-loaded plate at the yarn outlet. These five STEP components are in the clamp's coordinate system. Set both mounting references 0.0127 mm lower in local Y and fit the 0.0127 mm shim under the cup. The yarn's measured diameter and the assembled position determine which setup to use.

| Component | CAD |
|---|---|
| Jaw | [Jaw body](D01_jaw_A.step) |
| Bonded tail outlet | [Potting profile](D03_tail_resin.step) |
| Spring seat | [Cup](front_cup.step) |
| Ball retention | [Retainer](front_retainer.step) |
| Cup shim | [Shim](front_shim.step) |

The [shoe-travel data](shoe_travel.csv) follow 197 quasi-static equilibria along the recorded 0.600 mm yarn trajectory from 0 to 309.6 µs. Under this model the least remaining travel is 0.004834 mm, and the ball bearing stays under positive load. Direct steel-to-yarn force starts at 3.438 mN and reaches zero as the yarn moves onto the fixed pin. Each row gives the equilibrium at its specified yarn position. The calculation assumes time for the shoe to settle at each position.

To reproduce the table checks, run `python3 -m unittest benchmarks.test_outlet_travel` from the repository root. Confirm stock size, mounted depth, spring travel and preload on a physical assembly.
