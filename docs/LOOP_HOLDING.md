# Loop-holding mechanics

The holding model connects a three-dimensional active yarn bight to the hanging
clamp and six neighboring textile load paths. Their support locations and the20g
clamp target come from the fixture specification. Clamp translation and orientation
participate in equilibrium; active yarn endpoints are not fixed in space.

The potential energy includes nonlinear rod stretch/bending, finite-radius tool
and yarn contact, tension-only textile members and gravity mgz. The textile-member
law is EA*max(length-rest_length,0)^2/(2*rest_length). Slack members exert no
compressive force. The solve evaluates yarn forces, clamp force and clamp torque.

The textile members are a constitutive surrogate. EA, bending rigidity, effective
rest lengths and connection behavior are explicit model assumptions requiring
qualification for a chosen yarn/fabric. The CAD dimensions identify where supports
are located; they do not turn these assumptions into measurements. Alternative
head positions and a front-guide comparison are research inputs, not an adopted
operating program.

See `physics/loop_holding.py`, `spec/loop_holding.json` and the analytic/gradient
regressions in `tests/test_loop_holding.py`. The numerical tools support mechanism
research; passing a force-equilibrium check and completing a material transfer
are separate questions.
