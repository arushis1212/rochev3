# The sliding crochet gate

The hook holds the mouth of the yarn passage closed while its gate advances. A shallow cam on the gate brings its metal face into contact with the working strand. A narrow channel in the hook heel gives the cam room when the gate opens for service. The two brass parts use the existing slide. [Hook STEP](../cad/capture_gate/hook_with_heel_relief.step) · [Gate STEP](../cad/capture_gate/gate_with_cam.step) · [Part coordinate bounds and file hashes](../cad/capture_gate/geometry.json)

| Feature | Dimension |
|---|---:|
| Cam rise and flat width | 0.140 mm × 1.05 mm |
| Rise, plateau and descent lengths along the gate | 0.40, 0.47 and 0.40 mm |
| Heel channel width and maximum depth | 1.25 mm × 0.170 mm |
| Working advance from the closed position | 0.85 mm |
| Full service travel | 16.5 mm |

The complete service sweep gives a conservative lower bound of 0.07139 mm between the cam and hook on the nominal rigid solids. Allowing 0.020 mm for their relative alignment and 0.010 mm on each profile leaves 0.03139 mm. These are proposed inspection limits. The included STEP files are individual parts in their own coordinates.

For the modeled 0.550–0.600 mm yarn, a ±0.030 mm centerline allowance, ±0.010 mm cam profile and ±0.030 mm working command give 0.04285 to 0.17185 mm geometric overlap at engagement. That overlap calls for local yarn or hardware displacement. At 0.600 mm diameter a single freely moving normal coordinate settles 0.11879 mm away from its starting position under a 5.447 mN cam reaction, with the neighboring positions held. This result describes local capture mechanics. A yarn sample, profile inspection and a loaded full-cycle test establish the behavior of a fabricated pair.

## Slide load during engagement

The five sliding parts have an estimated total mass of 5.115 g at the modeled material densities. Opening the gate on the 30° incline lifts them by 0.425 mm and requires 25.079 mN against gravity. For a smooth 0.85 mm opening in two seconds, the modeled rigid-body inertia adds at most 0.00628 mN. With one yarn coordinate free and the original material law, the first contact occurs at 0.28495 mm. Across 27 positions the peak signed load is 26.30 mN. A continuous conservative bound is 97.29 mN before slide friction. Weighing the five parts and measuring the loaded slide force over the same stroke gives a direct bench comparison.

## Finishing the cam

Cut the replacement gate from a blank that includes the 0.140 mm rise. Its tightest longitudinal curvature radius is 0.19048 mm. A nominal Ø0.30 mm ball tool fits both ramps. With 0.016 mm maximum longitudinal interpolation and 0.025 mm transverse spacing, ideal chord error and scalloping together leave at most 0.00122 mm of material in the surface-normal direction. An independent CAD check placed the tool center at 420 locations across the face. Spindle runout, workholding, burrs and polishing enter the remaining machining allowance. Research on brass microchannels supports measuring these errors on a finished part. [Brass microchannel experiments](https://doi.org/10.1016/j.jmapro.2020.04.079) · [Runout experiments in CuZn37 brass](https://doi.org/10.1007/s00170-018-2678-2)

## Setting the working position on the bench

A removable gauge occupies 15.650 mm of the 16.5 mm stop slot. With the gate closed, insert the gauge from the top until its flange rests on the original plate. Keep the round nose seated against the rear of the slot and move the gate knob until its sleeve meets the gauge's flat face. This sets 0.850 mm nominal opening. The screw clears the seated gauge by 0.200 mm. Before lifting the gauge out, return the knob to its closed hard stop. The reverse insertion path has 0.4475 mm screw clearance. With the gauge removed, the gate can open fully. [Working stop STEP](../cad/capture_gate/working_stop.step)

The tongue is 3.260 mm wide and 2.50 mm deep. Inspect its fit in the actual barrel and measure displacement from the closed stop under the intended opening load. The detachable gauge acts as a bench setup reference. The original gate knob supplies the operator interface.

## A motor-driven gate option

A roller on an extended knob follows a disk cam. Three circular dwells hold the slide closed, at its 0.85 mm working opening, and at its 16.5 mm service opening. The working rise spans 36° and takes two seconds at 3 RPM. A 6 mm bearing runs on a 3 mm shoulder screw. The cam and knob STEP files share the head coordinate frame at closed. The camshaft is at U = −85.90, V = −2.30 mm and the roller center is at U = −101.40, V = −2.30, W = −19.50 mm. [Drive disk STEP](../cad/capture_gate/drive_disk.step) · [Roller knob STEP](../cad/capture_gate/roller_knob.step)

The disk profile offsets the roller-center curve inward by the roller radius. Each of its 720 CAD chords lies within 0.000916 mm of the ideal surface by the curvature bound. This allowance describes the CAD surface. Measure actual cam runout, roller play and loaded gate displacement at the dwells. The proposed 12 mm hub includes a keyed bore for the drawing’s 5 mm shaft and a radial M2 tap pilot for axial retention. Verify the received motor’s shaft dimensions before machining. [Roller-follower mechanics](https://doi.org/10.3390/machines11060604) · [Motor drawing](https://cdn-shop.adafruit.com/datasheets/28byj48dimension.jpg) · [Bearing dimensions](https://www.ezo-brg.co.jp/english/product/spec.php?eid=00179&unit=mm)

The extended knob and its roller hardware add an estimated 3.558 g to the moving slide. For the studied yarn path and 30° incline, the revised continuous load bound is 114.74 mN before slide friction and return force. At the maximum working slope that corresponds to 0.2911 N·mm at the camshaft. A bench test can measure these loads separately with the return spring removed and installed.

## Mounting the motor

A printed replacement barrel holds the motor on two M3 screws and a Ø9.030 mm pilot. Two upper ribs straddle the existing service slot. The motor tabs are 35 mm apart. A recess under the hub gives 0.250 mm nominal clearance, and the new roller axle clears the bracket by at least 0.750 mm throughout the 16.5 mm gate travel. [Motor carrier STEP](../cad/capture_gate/motor_carrier.step)

The bracket study includes its own weight, a 37 g motor and the aluminum cam at its computed center of mass. With the barrel interface held, a 2,000 MPa isotropic material model predicts at most 0.00513 mm of gate-axis motion under gravity with the disk at closed. The finest two meshes differ by 0.000031 mm. At this pose the predicted bracket compliance is 0.00909 mm per newton of axial contact force. To compare a print with the model, clamp the barrel at the same interface, install the drive, measure cam displacement as you turn the assembly under gravity, and apply a known radial force at the closed cam position. Record the print orientation, temperature and loading direction. [PLA material reference](https://store.bblcdn.com/s7/default/3df0c03989c349d082e758e5d62c813b/Bambu_PLA_Basic_Technical_Data_Sheet_bf3411ce-be39-4db7-9669-1b4671d2196b.pdf)
