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

## Returning the slide

The spring-compatible knob and motor carrier add two pin mounts on the side opposite the motor. A Lee Spring EI 010C 06 M pulls the roller toward the cam. The two Ø2 mm pin surfaces give an inside-loop length of 25.00 mm at closed, 25.85 mm at the working opening and 41.50 mm at service. The catalog load law gives 0.330, 0.363 and 0.974 N at those positions. With the two mounts installed, measure the return load in both directions and the breakaway force right before the gate closes. The model allocates 0.210 N at closed for additional drag and load variation along the studied working return. [Spring-compatible knob STEP](../cad/capture_gate/spring_roller_knob.step) · [Spring-compatible carrier STEP](../cad/capture_gate/spring_motor_carrier.step) · [Manufacturer's stock spring tables](https://www.leespring.com/sites/default/files/2019-07/Lee_Spring_Catalog_US_Eng.pdf)

Gravity acting on the eccentric aluminum disk can also load the motor at a dwell. With the solid reference disk, including that torque and the nominal return spring gives 2.165 N·mm for the modeled working rise. Service rise and return give up to 11.67 N·mm before service yarn load, friction or transient acceleration. Measure running torque and gate travel with the actual motor, driver and spring. Use the two spring-compatible parts together.

## Installing the pocketed service cam

The pocketed aluminum disk uses a revised service lift and two 2.5 mm deep pockets. The 0.85 mm working lift still takes two seconds at 3 RPM. The 7.56 g disk has a 4.60 mm center-of-mass offset. With the stock spring, slide weight and disk gravity, modeled torque reaches 8.14 N·mm on the service rise and 8.34 N·mm on the return. Measure shaft friction, service yarn load and running torque before selecting an operating speed. [Pocketed cam STEP](../cad/capture_gate/spring_drive_disk.step)

Mount the motor on the spring-compatible carrier at the bench. Before fitting the follower and spring, introduce the disk from the open side with its hub 8.50 mm off its seated axial position. Move it 66 mm along positive V to the shaft axis, then seat it along W. Turn the set screw toward the tool port at 275° from positive U when viewed from positive W. A 1.20 mm tip, 2.50 mm shank and 18 mm handle clear the modeled carrier by at least 0.40 mm. Size the double-flat bore to the measured shaft. [Carrier with tool access](../cad/capture_gate/spring_motor_carrier.step)

## Supporting the roller and spring

The spring and roller press on opposite sides of the slide. Two printed ribs carry that load back to the gate-tail fastener. The revised knob adds 1.80 g at the reference PLA density and leaves 0.55 mm for side insertion of the captive roller nut. Under the catalog spring load, the finest elastic mesh predicts 0.00657 mm working deflection and 0.01768 mm service-return deflection with the gate tail held over a 2.20 mm radius. Reducing the assumed support radius to 1.80 mm gives 0.01222 and 0.03297 mm. Measure the loaded position at the gate after assembling the actual tail, bolt and sleeve. With the added slide mass, the known service torque reaches 8.33 N·mm on rise and 8.53 N·mm on return. [Reinforced roller knob STEP](../cad/capture_gate/reinforced_roller_knob.step)

To park the roller at the nominal acquisition position, approach in the opening direction from a measured angular datum. At the supplier’s nominal 516.096 full steps per output turn, step 33 corresponds to 0.2155 mm on the ideal cam. The modeled stationary acquisition band for the 0.600 mm yarn is 0.187–0.247 mm. Measure the assembled opening, then release the material with the cam parked. This setting depends on the actual gear ratio, indexing, spring load and yarn stock. [Motor specification](https://www.adafruit.com/product/858)

## Machining the outer rim

The current pocketed cam has 150 smooth spline edges and three exact circular dwells. Adjacent edges share their position, tangent and curvature. The nominal machined rim stays within 0.000083 mm of the continuous roller-offset curve by the subdivision bound. Inspection of the exported STEP at 727 stations gave a maximum discrepancy of 0.000000036 mm. These values describe the CAD. The completed part also depends on tool runout, setup and controller accuracy. [Continuous cam rim and pocketed disk](../cad/capture_gate/spring_drive_disk.step)

The separate tool-center wire follows the axis of a 3.000 mm cylindrical cutter around the exterior. Both files use the same shaft datum. Choose the part outline when CAM applies radius compensation, or the pre-offset wire with compensation disabled. Set cutting depth, workholding, feed and entry for the machine being used. [External milling centerline STEP](../cad/capture_gate/external_mill_center.step)

## Setting the capture opening without a camera

At the P5 swatch station, an inclined steel shoe meets the outside of the follower's Ø5 mm shoulder-screw head. The return spring seats the follower on that face while the disk stays at its closed dwell. This lets the physical position of the head determine the gate setting continuously. The assembled stand, sliding foot, receiver and example fasteners use machine-world coordinates. [Station gauge STEP](../cad/capture_gate/station_gauge.step) · [Machined steel shoe](../cad/capture_gate/setting_shoe.step)

For the modeled 0.600 mm yarn, set the opening in millimetres to 0.202 + 3.2 times the transverse displacement of the head in millimetres. The evaluated head range is −0.010 to +0.050 mm. A local simulation using both 0.130 and 0.150 mm gate rises and the two extreme placements gives first contact at 247–367 µs and release at 261–377 µs. Each run uses the complete installed stock and finite yarn geometry surrounding this stitch pose. [Four capture and release cases](../examples/station_capture.json)

The nominal fixture locates a 0.217 mm opening at zero transverse offset. A measured 0.02044 mm shim at its positive-Y fence adjusts the intercept to 0.202 mm. Use a dimensional reference to measure the loaded brass gate at both ends and the middle of its travel. For the tolerance calculation above, the total setting error including measurement uncertainty must stay within 0.012 mm. With ideal fixture joints the modeled shoe and post move by 0.00621 mm at 2 N, expressed as gate displacement. Record the actual load and temperature during calibration. For removal with the head parked, open to 0.85 mm, remove the locking screw, slide 12 mm toward −Y and 40 mm toward +X, then lift. [NIST dimensional comparison handbook](https://www.nist.gov/system/files/documents/calibrations/mono180.pdf)
