# Coupled material handling

The numerical fixture now connects the old bight to the captured working strand
through a shared cloth-clamp attachment. Ordered material edges retain their
reference lengths and identities. Both spans contribute to clamp force and torque;
solid contact, yarn self-contact and gravity act on the entire route.

The working strand passes through the closed hook aperture without a node being
attached to the hook. Its guide approaches through the open end of the actual
hollow tube. A point 2mm in front of the guide defines the initial threading bend.
[Coordinates and accepted states](CONNECTED_MATERIAL.json) accompany the model.

The carriage and fixed-anchor contact models use unions of enclosing boxes for their additive CAD
primitives. A native-solid subtraction test verifies complete coverage while
retaining the open yarn corridor. Guide-tube distances use the exact annular
cylinder geometry and are checked against independent CAD distances and gradients.

`physics/connected_yarn.py` implements the coupled energy and derivatives;
`physics/guide_contact.py` provides the nominal tube contacts. The regression
suite checks the shared-node force/torque chain rule and contact geometry. A
contact-scale Newton stencil resolves shallow active contacts. Exact segment/AABB
culling evaluates the original reference-quadrature samples only where a contact
penalty can be nonzero. Dense-oracle tests check identical energies and forces;
a bounded secant predictor supplies an initial guess without changing constraints.
The current T14 dataset contains five freshly evaluated saved states, starting
at advance0.001785714mm and ending−1.107142857mm, with force, capture,
clearance and centerline-interpolation checks. The lower stripper slots widen
to halfwidth1.45mm belowv2.5 and taper back to1.0128mm byv3.5.

These are synthetic, quasistatic component experiments with one old bight and a
locked guide material endpoint. Two-loop single-crochet formation, metered feed,
material qualification and physical demonstrations determine the next stage.
