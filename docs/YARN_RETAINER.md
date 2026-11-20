# Spring-mounted yarn retainer

A steel ball on a narrow leaf spring supports one arm of the yarn near the closed hook. The support can move with the strand as the guide approaches. The ball diameter is 2 mm. The blade is 1.0 mm wide and 0.10 mm thick, with an 11.75 mm free span between its bonded ends.

| CAD part | Role |
|---|---|
| [Spring cup](../cad/yarn_retainer/spring_cup.step) | Locates the steel ball and receives the blade. A groove leaves a nominal 0.020 mm adhesive film over 1.866 mm². |
| [Spring mount](../cad/yarn_retainer/spring_mount.step) | Supports the root of the bent blade and provides a mouth for its movement. |

The files use millimetres and share the installed machine coordinates. Each STEP file contains one solid. Import both without recentering to see their relative positions. The [geometry record](../cad/yarn_retainer/geometry.json) gives their volumes, centroids and file hashes.

The modeled tip assembly, including the ball, cup, adhesive and attached steel, has a mass of 38.931 mg under the study’s material assumptions. A transient simulation followed the mounted retainer through 70 µs, with a minimum 0.4296 mm modeled separation from surrounding machine hardware on the nominal swept cases. These dimensions describe the retained-yarn experiment. [Main machine CAD](../cad/machine/generated/machine.step)
