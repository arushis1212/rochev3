# Material-conserving feeder mechanics

The upstream model extends a material chain through the175mm guide, an axial
fairlead, two fixed grooved pulleys, a translating pulley and the closed nip.
Each reference edge length is assigned once at manual threading. The guide
mouth is an interior material point; payout comes from redistribution of that
finite supply, rather than an artificial increase in reference lengths.

With pulley height Z and counterweight height Zc(Z), gravitational potential is
V=0.00980665*(12.848*Z+9.789*Zc) Nmm in LOW mode. The existing finite-radius
constant-cord constraint determines Zc and its derivative. The feeder equation
adds dV/dZ to the opposite of the yarn contact reaction on the moving pulley.
Executable tests compare virtual work and contact action/reaction against
independent finite differences, and fairlead distances against native CAD.

The proposed initial route uses an axial fairlead entry at[109,406,238]
and an axial nip entry at[24,406,238.8], in global millimetres. The fixed nip is
at[16,406,238.8]. Groove radius is8mm; the initial polygon accounts for0.3mm
yarn radius. Travel is130<Z<190mm. R06 uses a seven-piece conservative cover
verified to contain the native anchor while preserving its open center.

This is an ideal frictionless quasistatic formulation with declared synthetic
stiffness and manually initialized material. It supplies mechanics tools for
coupled feeding studies; its scope does not establish a connected stitch cycle.
Physical gripping, material calibration and continuous replenishment are separate
qualification stages. Run the test suite using the README instructions.

The T15 whole-material study uses95 nodes and804.5309777608705mm of fixed reference material. Five saved equilibria extend from advance−1.107142857 to−3.078571429mm, with a solved feeder height and no fixed material point at the guide mouth. Each saved endpoint passes the stated force/contact checks and an upstream check against557 native solids. Linear interpolation certificates cover centerline noncrossing. [Endpoint data](WHOLE_FEED.json) and [material coordinates](FEED_CHECKPOINT.json) retain these scoped quantities. The installed fairlead screw isM3×14, preserving full nut engagement and1.7mm nominal yarn clearance.
