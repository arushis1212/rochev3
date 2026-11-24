# Sprung cloth clamp

The cloth clamp holds the hanging fabric and carries the yarn outlet. A steel contact, acetal pressure shoe, keyed return pin and M2 spring plunger locate the yarn and react to its load. Open the assembly for the yarn diameter being studied.

| Yarn diameter | Installed solids | Assembly |
|---|---:|---|
| 0.575 mm | 31 | [Download STEP](0p575/assembled_P5_clamp.step) |
| 0.550 mm | 30 | [Download STEP](0p55/assembled_P5_clamp.step) |

Coordinates are in the clamp body frame, in millimetres. The [parts register](PARTS.json) maps each assembly to its component instances and separate part files, including shared files between the two sizes. The register also lists solid volumes, centroids and bounds. The full assemblies contain the hardware at its fitted position.

In the modeled stationary position, recomputing the forces on 357 yarn and fixture coordinates gave a maximum imbalance of 23.102 nN on the 0.575 mm stock and 24.252 nN on the 0.550 mm stock. Each falls below the 100 nN numerical criterion for this case. The springs, hardware masses and fabric loading are part of that calculation. The assembled prototypes provide the reference for measuring actual clearances and spring preload.
