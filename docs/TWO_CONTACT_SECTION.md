# A yarn section against two supports

When yarn touches two nearby surfaces, pressing against one surface can change the gap to the other. A two-direction compliance model describes how one material section responds. It can serve as a small analytical benchmark for a larger rod model.

Let **g** contain the two signed clearances before deformation. Let **p** contain the two compressive loads. A symmetric positive-definite matrix **C**, in mm/N, maps those loads to changes in clearance. The final gap is **w = g + Cp**. Each load and final gap must be nonnegative, and each pair satisfies **pᵢwᵢ = 0**. These conditions give four possibilities. The section can clear both supports, load either support alone, or load both. The calculation evaluates those cases directly.

For illustrative diagonal compliances of 0.40 and 0.30 mm/N, reciprocal cross-compliance of 0.12 mm/N and initial gaps of −0.12 and −0.09 mm, the loads are **0.23864 N and 0.20455 N**. Both gaps close. The stored elastic energy is 0.023523 N·mm. Its derivative with respect to either initial gap equals the negative reaction in that direction. The tests check this virtual-work relation inside contact regions and at a change of contact.

The coefficients describe a hypothetical section. To fit a real yarn, hold axial tension fixed, apply independent normal loads in two directions, and observe the displacements in both directions. Subtract the fixture compliance and check the result under a separate simultaneous-load case. A single compression curve leaves the cross-coupling undetermined. Friction, large deformations and loading history require additional measurements.

Run `python3 examples/two_contact_section.py` for the printed reactions and energy. [Calculation](../examples/two_contact_section.py) · [Analytical tests](../benchmarks/test_two_contact_section.py)
