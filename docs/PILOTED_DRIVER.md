# Piloted service driver

A removable tool reaches a captive screw beneath each of Roche’s four support stations. Its hex flats transmit torque. A short pilot engages the bore at the floor of the socket. A second cylindrical journal engages the sleeve on the head of the screw. These two guides support the tool on opposite sides of the loaded flats.

| Interface | Design range |
|---|---:|
| Driving section across flats | 2.46–2.49 mm |
| Socket across flats | 2.55–2.60 mm |
| Outer journal diameter | 3.0120–3.0135 mm |
| Outer sleeve bore diameter | 3.015–3.018 mm |
| Inner pilot diameter | 1.806–1.808 mm |
| Inner bore diameter | 1.813–1.815 mm |
| Straight hex engagement | 1.00–1.20 mm |

The installed CAD study covers four service states at each of four stations. The tool clears all sixteen access routes with a minimum exterior bound of **0.8161 mm** against a **0.8000 mm** requirement. A separate mating study moves the tool from first entry to torque take-up. All 160 prescribed poses had zero measured solid overlap. The first station’s forty poses can be replayed directly against the complete shaft and screw STEP solids. The recorded center, rotation pivot, pose coordinates and reference gaps are in millimetres and degrees. [Complete driver shaft](../cad/service_driver/matched_driver.step) · [Driving tip](../cad/service_driver/driver_tip.step) · [Captive screw](../cad/service_driver/station0_pin.step) · [Service poses](../cad/service_driver/service_poses.json)

From a checkout with CadQuery installed, run the example to compare every pose with the recorded overlap and clearance. The screw uses installed coordinates and the tool uses its local machining coordinates. The dimensions and results describe this component study. [Replay program](../examples/service_driver.py)

```sh
python3 examples/service_driver.py
```


## Flexural shank

A 19.8–20.2 mm long section, turned to 0.82–0.86 mm diameter, lets the journal tilt as it enters the sleeve. Smooth changes in radius join it to the main shaft and the journal. The STEP solid reaches the grip mounting face. A coplanar calculation of two-wall sliding reviewed 512 dimensional corner combinations. At friction coefficient 0.40, the largest modeled insertion resistance was 1.844 N against the design’s 2 N limit. The calculated first elastic buckling load was at least 8.08 N in the tested dimensional cases. These values apply to straight-sleeve entry with the specified shaft restraint. The working flats, leading pilot and screw are shared with the tip-only study.
