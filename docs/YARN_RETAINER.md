# Spring-mounted yarn retainer

A steel ball on a narrow leaf spring supports one arm of the yarn near the closed hook. The support can move with the strand as the guide approaches. The ball diameter is 2 mm. The blade is 1.0 mm wide and 0.10 mm thick, with an 11.75 mm free span between its bonded ends.

| CAD part | Role |
|---|---|
| [Spring cup](../cad/yarn_retainer/spring_cup.step) | Locates the steel ball and receives the blade. A groove leaves a nominal 0.020 mm adhesive film over 1.866 mm². |
| [Spring mount](../cad/yarn_retainer/spring_mount.step) | Supports the root of the bent blade and provides a mouth for its movement. |

The files use millimetres and share the installed machine coordinates. Each STEP file contains one solid. Import both without recentering to see their relative positions. The [geometry record](../cad/yarn_retainer/geometry.json) gives their volumes, centroids and file hashes.

The modeled tip assembly, including the ball, cup, adhesive and attached steel, has a mass of 38.931 mg under the study’s material assumptions. A transient simulation followed the mounted retainer through 70 µs, with a minimum 0.4296 mm modeled separation from surrounding machine hardware on the nominal swept cases. These dimensions describe the retained-yarn experiment. [Main machine CAD](../cad/machine/generated/machine.step)


In a subsequent transient simulation, a nominal 0.600 mm yarn reached the printed cover at 172.583 µs and detached at 183.326 µs. The largest sampled normal reaction at the cover was 86.56 mN. The two guide spans could move while the yarn outside them was held. Throughout the 155.524–240.000 µs window, the ball applied normal pressure to the retained arm. Measured along a fixed normal from the retained arm toward the working arm, the entire sphere stayed at least 0.2984 mm behind the retained centerline. The closest approach of that working yarn to the ball surface exceeded 0.5988 mm. These dimensions and forces describe the simulated contact conditions.
