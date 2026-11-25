# Yarn at the feeder, spring tips and forming gate

The yarn reaches a sprung guide at the feeder, remains held by two spring tips, and loads a separate forming gate. The following models use the registered geometry and distinguish each station's load and motion.

| Interface | Reproduced result |
|---|---|
| Feeder outlet on 0.600 mm yarn | A 55-edge strand with 52 moving material nodes and 53 freely spinning sections produces 10.998 mN peak shoe force over 309.6 µs. The previous time refinement gives 10.997 mN. Least clearance among 50,714 eligible nonlocal strand pairs is 0.08186 mm. |
| Laminated spring carriers | Both tips stay on the intended strand in 960 modeled combinations of stock diameter, time and three-axis installation errors. The least clearance to another eligible edge is 0.07328 mm. At assumed friction coefficient 0.275, the least ideal axial traction ceiling is 3.277 mN. |
| Forming gate under approaching yarn | The complete parked gate equilibrates on 18 compressive supports. When the yarn touches, both components respond to the contact force. Two independent clocks give 0.3138505 and 0.3138503 mN at 305.700 µs, with a 0.3344% difference in accumulated contact impulse. |

The feeder calculation combines axial extension, bending, twist, translational and rotational inertia, gravity and finite steel contact. The 55-edge test imposes the outside strand motions and clamp motion. The carrier calculation uses actual brass plates, steel shims and leaves, solder, printed sockets and cured epoxy. Dry faces transfer compression and can open. The gate calculation couples full elastic and rigid-body motion to the moving yarn. The quoted intervals cover the first modeled engagement of each interface.

The printable carrier kits include size-specific coupons and inspection dimensions. The formed foil is a separate component fit study on the 0.600 mm feeder. [Carrier kits](../cad/spring_carriers/BUILD.md) · [Machined foil and fit calculator](../cad/feeder_ball_retainer/README.md)
