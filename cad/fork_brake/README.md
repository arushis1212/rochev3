# Receiver fork brake

A profiled cam moves a spring-loaded roller and a straight 0.8 mm steel pushrod. The rod enters a blind bore on the fork’s center-of-mass line. The cam turns at 45 rad/s during entry and braking. The later transfer and return sectors have a 10 rad/s design speed. The two return springs seat the roller on the working flank throughout the cycle.

The model enters at 181 mm/s and uses 0.102 mm of fork travel to stop. The elastic calculation includes the fork mass and one-third of the rod mass. The cam’s acceleration ramps are timed to cancel the nominal axial vibration at the end of braking. The benchmark integrates the differential equation from the incoming speed and repeats the calculation at five modal frequencies.

Run `python3 examples/fork_brake.py` or `python3 -m unittest benchmarks.test_fork_brake` from the repository root. The STEP assembly contains the fork drive subassembly in machine coordinates. The annular solids surrounding the two guide rails show the volume occupied by the compression springs over travel. The material moduli, spring preload, mounted frequency and friction are design inputs for prototype measurement.
