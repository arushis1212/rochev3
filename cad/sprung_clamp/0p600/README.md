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

The [moving-shoe trace](moving_shoe.csv) follows all 1,703 recorded yarn positions with inertia of the 0.923575 mg steel shoe and tab and the effective moving portion of the two blades. The total modeled translating mass is 3.603915 mg. The undamped axial simulation gives a peak force of 85.783 mN on the prescribed yarn and preserves 0.00317 mm of travel to the positive stop. The spring plate responds on a comparable time scale to the change in yarn position. This model predicts the shoe response to a given yarn path.

To reproduce the table checks, run `python3 -m unittest benchmarks.test_outlet_travel` from the repository root. Confirm stock size, mounted depth, spring travel and preload on a physical assembly.
