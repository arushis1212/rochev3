# Rear carriage index

Three dimensioned parts move the S1 indexing pin to the rear of the bed and leave the main guide in its parked pose. The pin locates the carriage along its travel axis. Two side guides accommodate lateral motion of the strap.

[Bed and index yoke](B01_bed.step) · [Support carriage and slotted strap](B03_carriage_1.step) · [Index pin](B09_index_pin_1.step)

Machine axes are X across stations, Y along carriage travel and Z upward. All sizes below are finished millimetres. Parent bed mounting features and the S1 mounting seats use their existing finished drawings.

| Part | Finished geometry and inspection |
|---|---|
| B03 carriage, S1 only | One-piece carriage and strap. Strap is centered at X136, Y226–381 in the home pose, Z80.0–82.4. Width 7.50 ±0.05, thickness 2.40 ±0.05. Four transverse capsule slots measure 4.30 ±0.05 in X and 3.09 ±0.02 in Y. Their center Y coordinates in the home frame are 373, 362, 356 and 331. Mark the corresponding carriage positions −17, −6, 0 and +25. Control finished Y position of each slot relative to the machine datum within the shared 0.040 mm longitudinal datum budget, checked in assembly. |
| B01 bed | One-piece bed, rear keel and pin yoke. Original rear bed face is Y260. The 16 mm wide keel blends into the bed floor with a relieved shoulder. The yoke spans Y350–362. Lower cheek Z70–77, upper cheek Z85–91. Finish the opposing side guides to a clear width of 8.10 ±0.05 centered at X136. Maintain guide-center to active-bore-center error ≤0.05. Set Z limits and yoke-axis positions within ±0.05 unless tighter tolerances are given. |
| B09 pin, S1 only | One-piece turned metal pin. Shaft 2.995–3.000 diameter, 19.50 ±0.05 under the head, with a 0.25 × 45° tip chamfer. Head Ø8.00 × 6.00 high. Top of the seated pin is Z97. The head bearing face is Z91, with the nominal tip at Z71.50. Working hole center X136/Y356. Storage center X120/Y356. |
| Finished fixed bores | Diameter 3.04–3.06, nominal 3.05. Machine both cheeks in one setup using a supported pilot and line reamer. Limit residual lateral axis mismatch and shaft radial bow to 0.005 each. Active bore extends to Z69. Maximum pin tip penetration leaves 2.5 mm nominal bottom clearance. Shaft overlaps lower cheek by 5.5 mm at the nominal seat (5.25 mm full diameter before chamfer). The parking hole is in the solid side pillar. |

For the printed route, print the complete strap flat with continuous longitudinal roads through the root and slot ligaments, then finish the side and hole surfaces. Locate the yoke and carriage against their actual machine datums before final sizing and marking. The modeled roof can be bridged or printed with removable support and finished from its open ends. Check all four detents for full insertion by hand. If the printed lot misses the coupon stiffness or fitted-part gauges, the alternate machined-metal route uses the same STEP geometry. A printer or material name alone supplies no modulus, straightness or registration evidence. Retain a fitted pin, bed and carriage together.

## Service and load case

1. Stop the head and guide at the registered two-loop pose. Hold S1 against longitudinal load before touching the pin. Use the opening on the left side of the machine. The checked rectangular entrance spans X−10 to +145, Y347–365 and Z92–133.
2. Lift the pin vertically 22.0 mm. Its tip reaches Z93.5, clearing the upper cheek by 2.5 mm. Move it 16.0 mm toward negative X and lower into the storage hole. Keep the carriage stationary until it is parked.
3. Move S1 with the operator holding the carriage. The stored pin stays on the fixed bracket while the strap passes between the guide cheeks. Align the desired detent marking and bring the carriage to rest.
4. Reverse the parking path, then lightly adjust S1 along Y while lowering the pin. Seat its head against the upper cheek. Verify full seating and longitudinal registration before applying yarn load. A carriage collision or excluded yarn contact elsewhere in the machine requires its own motion clearance.

The left-side check models an 18 mm wide finger or gripper access cross-section through to the pin and its entire 22 mm lift. A production gripper, hand, grip force and automatic lock sensor require their own sizing.
