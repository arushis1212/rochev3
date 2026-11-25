# Yarn at the feeder, spring tips and forming gate

These calculations use the modeled yarn and registered machine hardware. Each station has its own loading and boundary conditions.

| Interface | Reproduced local result |
|---|---|
| Feeder outlet on 0.600 mm yarn | Over 309.6 µs, the coupled axial shoe and 13 moving yarn nodes reach 10.981 mN peak contact force. Independent evaluation on the steel CAD surface gives 10.981 mN. All 16 interacting yarn edges are checked across the time cells. |
| Laminated spring carriers | In 135 combinations of yarn diameter, two installed tip offsets and five sampled times, both tips retained the intended yarn segment. Normal forces range from 5.906 to 11.664 mN. Minimum clearance to another eligible strand edge is 0.09149 mm. |
| Forming gate in its parked seat | Eighteen compressive support reactions balance the 53,700-coordinate elastic model. The largest elastic force residual is 4.0 × 10⁻¹¹ N. Independent checks cover the complete front and rear faces and the two steel floor surfaces. |

The feeder study uses yarn extension, bending, rotational and translational inertia, gravity, finite contact and the installed spring mass. Four outside material nodes, the clamp pose and shoe slopes drive this local interval. For the spring carrier, the actual laminated brass plates, steel shim, solder, leaf, printed socket and epoxy enter the compliance calculation. At a friction coefficient of 0.275, the least computed ideal axial traction ceiling is 3.292 mN. Actual grip depends on yarn, finish and assembly. [Size-specific carrier kits and inspection](../cad/spring_carriers/BUILD.md) · [Feeder ball and retainer CAD](../cad/feeder_ball_retainer/README.md)
