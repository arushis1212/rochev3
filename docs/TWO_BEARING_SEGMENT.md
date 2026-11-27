# Two supports on one strand

A yarn segment can touch two surfaces at once. Both contact points matter when the hook changes direction and the load shifts between its bearing surfaces. This example has an exact solution that can be reproduced with Python's standard library. [Code](../examples/two_bearing_segment.py) · [Tests](../benchmarks/test_two_bearing_segment.py)

Place an 8 mm straight segment above two round pins centered at (2, −0.9) and (6, −0.9) mm. Give the yarn a 0.3 mm radius and each pin a 0.6 mm radius. Both pin surfaces touch the yarn. The two contact normals point up, at fractions 0.25 and 0.75 along the segment.

Apply downward loads of 2.5 mN and 3.5 mN at the segment's endpoints. Vertical force balance requires the two upward pin reactions to sum to 6 mN. Taking moments about the left endpoint gives `2 F₁ + 6 F₂ = 8 × 3.5` in mN·mm. The solution is **2 mN on the first pin and 4 mN on the second**. A model using only the first contact could balance the total force with 6 mN, but it would leave a 16 mN·mm moment.

Run `python3 -m examples.two_bearing_segment` from the repository root. The result describes a straight finite element with two fixed, frictionless round supports and a known transverse load. The same force and moment equations test a contact implementation without depending on a particular machine geometry.
