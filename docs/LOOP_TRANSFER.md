# Mechanically registered transfer station

The T14 research fixture combines a closable hook, paired stripper plates and a
vertically guided two-pin carriage. Its 52 local physical parts include the full
hook bearing/barrel hardware, a 16.5mm gate stop, a 6mm lift stop and a separate
6mm axial pin shuttle. The transfer experiment advances the hook 8.75mm, lifts
the registered bight, closes the gate and retracts the hook to advance -8.5mm.

The tall lift ear is at localu46…49mm. Outboard arms at|w|20…24mm connect its
fixed stop to the anchor. A printed frame bracket joins this station to the right
knockover post using the existing mounting holes and M3×30 replacement bolts.
The integrated single-station assembly contains557 nominal solids. Individual
STEP/STL files and an assembled STEP are in `cad/transfer/installed`.

The stripper plates retain their 1.6mm inner channel. Lower slot halfwidth is
1.45mm fromv−2.3 tov2.5, tapering back to1.0128mm byv3.5. Upper retention
geometry and the mounting interfaces remain unchanged. Lift pins are1mm diameter,
with their active axes atw±2.5mm. A two-pin shuttle slides along a3.175mm sleeve;
its6mm body moves between stop faces12mm apart, giving6mm travel. The pin tips
then reachu3.3744mm, beyond the front plate'su2.4256mm face. The finite-radius
withdrawal allowance for the0.3mm reference yarn radius is0.6488mm.

The guide crosses at local[15,20,-7]→[15,20,16], aligns to[10,20,16], then lowers
to[10,0.5,16]mm. These are commanded prototype positions in the documented frame.
The shared JSON and CadQuery builders define the geometry and all four manual
motion coordinates. Pin/rod retention uses explicit screws and captive nuts.

A203-state,197-target synthetic local bight experiment supplies force and contact
evidence. The current geometry is also checked at ten installed positions and
four axial-reset/lift positions. These are scoped quasistatic and nominal-geometry
studies supporting mechanism development. Hardware is a research prototype;
material qualification and connected stitch demonstrations define its application.

```sh
.venv/bin/python cad/transfer/build.py
.venv/bin/python -m cad.transfer.installation
```

The inherited whole-assembly instance keys for the two right-post bolts retain
`M3x16` in their names; the installation builder and inputs explicitly replace
those two bodies with M3×30 bolts. Use the installation specification for that
subassembly. No purchase or fabrication release is implied by nominal CAD.
