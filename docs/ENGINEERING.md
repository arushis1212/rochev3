# Mechanism and mathematics

Global X spans the stitch stations, Y points rearward and Z points upward.
Lengths are millimetres. The numerical specifications define finished profiles,
running fits and assembly datums; CadQuery constructs the corresponding solids.

The main hook has independent translation, roll and a sliding closure. Paired
supports register prior loops. The separate transfer module uses stripper plates
and retractable pins, carried on a captured indexed stage with a physically keyed
shoe. Two retained nips and a supported counterweight provide explicit service
interfaces for the moving-pulley feeder. Manual controls expose each operation
for instrumented prototype development.

The lower stripper window has a1.800 mm halfwidth. Subtracting0.050 mm edge
error,0.8255 mm hook halfthickness,0.600 mm yarn diameter,0.200 mm combined
registration,0.010 mm deflection and0.010 mm burr leaves0.1045 mm reserve under
those drawing admissions. Critical fits must be finished and inspected after printing.

Four matched2.50 mm spacers set the hanging-clamp jaw separation. A captured
3 mm pin permits a free return wrap between actual gripping lands. Flush
DIN7991 screws sit in the front jaw. Full-solid volume and declared densities
give an18.9359749 g reference mass; weighing and balancing supply actual inputs.
The clamp datum has six rigid-body degrees of freedom and gravity acts at
c+R*b_COM, where R=Rz(yaw)Ry(-pitch)Rx(roll).

For vertical frictionless yarn legs, moving-pulley tension is approximately
mg/2, or(m−mc)g/2 with the counterweight connected. The actual geometry uses
finite-radius tangent lengths and wrap arcs. Its nominal effective cord length
is214.706745509 mm;350 mm is the rough cut before seated terminations and trim.
Material properties, drag and grip behavior require measurement for hardware predictions; numerical examples use declared benchmark assumptions.

Rod energy combines stretch EA(l−l0)²/(2l0), discrete bending
2B(1−cosθ)/(lbar(1+cosθ)), finite-radius contact and gravity. Examples test
analytic limits and energy gradients. Collision-aware steps use the1-Lipschitz
distance bound: clearance decreases by no more than bounded relative movement.
Material conservation, force equilibrium and geometric admissibility are checked
separately. These numerical models state their constitutive and boundary assumptions.

Material-bound aperture diagnostics follow actual reference coordinates through
nonplanar loop geometry. Oriented segment/triangle intersections identify
passage direction and material location; finite boundary clearance and virtual
neck closure are reported separately. The diagnostic preserves the distinction
between geometric passage and physical loop retention.

Named contact-event monitors retain the original yarn quadrature and component
distances. Relative material and pulley motion bound each trial gap change,
including events inside a step whose endpoints are both clear. Buffered
activation and separation can limit a numerical search step while the physical
energy and force criteria remain unchanged.

Capture actuation uses an explicit affine map for head and guide translations
and the sliding hook closure at fixed roll. Each axis carriage carries its
downstream rails, tools and fasteners. The guide stage's rotated frame is
accounted for in world coordinates. Analytical contact components receive the
same translation as every native solid they cover; missing coverage or mixed
motions within one component are rejected. This kinematic mapping is separate
from travel, swept clearance and force checks.

Continuous aperture checks cover each affine material step using interval
triangle orientation and relative-motion distance bounds. A finite projection
search verifies the same3D disk without changing its material coordinates or
triangulation. [The method](APERTURE_GEOMETRY.md) separates diagnostic geometry
from forces and physical loop retention.
