# Mechanically guided loop transfer

The T8 research subassembly combines a sloped pocket heel, paired stripper plates,
and two guide pins on a printable lift carriage. The plates resist axial movement
of the old bight. After the hook advances8.75mm, the pins rise6mm before the slider
closes. The hook then retracts through the raised bight.

The mechanism has editable CadQuery source in `cad/transfer/build.py`, numerical
inputs in `spec/transfer_candidate.json`, and individual STEP/STL parts under
`cad/transfer/generated`. It is a separate mechanism study alongside the D22
assembly. Its contacts use the same authored metal profiles as the CAD.

For independent rigid bodies, the contact potential sums each active unilateral
penalty rather than discarding simultaneous surface reactions. An analytic
symmetric two-plane test checks both energy and force balance. Geometry tests
compare the exported contact surfaces with independent OpenCascade distances.

The local rod experiment uses declared synthetic yarn properties and a freely
translating/rotating hanging clamp with neighboring tension-only textile members. A completed numerical transfer is evidence for that model;
material qualification, connected crochet topology, and integration determine its
application to a complete machine. The lift carriage, rods and plates provide
concrete parts for studying mechanical registration and yarn handoffs.

T8 places the anchor and channel spacer at localv18…24mm, above the transfer
region. Guide rods are32mm long. The two M3 nuts are held30degrees from the
reference orientation, giving0.5mm nominal flat-to-flat separation. The plates
are36×20×1.6256mm; their inner faces define a1.6mm channel. The guide-axis
location is5.7256mm and nominal carriage-to-plate separation is0.30mm.

Auxiliary part envelopes participate in the contact calculation. The exact
46-part nominal assembly has been checked at five named mechanism poses.
A joined 203-state, 197-target local bight route reaches the castoff endpoint.
The full head hardware includes a 16.5mm positive gate stop. A sleeve and slotted
ear limit the manual lift to 6mm. Lateral M2 screws and trapped nuts retain the
two lift pins; additional M2 clamps locate the guide rods. The pin embed length
is 12mm. Two 3.4mm frame-interface ports lie at localv24mm,w±7mm.
These ports define the attachment interface for subsequent installation work.
These local dimensions and calculations belong to the transfer research fixture.
