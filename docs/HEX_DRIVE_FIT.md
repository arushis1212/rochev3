# How closely must a hex drive fit?

Roche’s removable service tool has two jobs. It must enter a small hex socket with some angular misalignment, then locate the screw axis within a lateral tolerance. Those requirements put an upper and a lower bound on the width of the straight driving section. The example lets you change the tool and socket assumptions and see their effect before machining a matched pair.

| Input to the worked example | Value |
|---|---:|
| Socket width across opposite flats | 2.550–2.551 mm |
| Maximum center offset after insertion | 0.010 mm |
| Combined profile-to-axis eccentricity | 0.0005 mm |
| Maximum axial reach | 1.435 mm |
| Maximum clock angle about axis | 0.20° |
| Maximum tilt between axes | 0.15° |

**The calculated driver interval is 2.534546–2.536360 mm across flats.** It includes a proposed gauged tool of 2.535–2.536 mm. The interval spans 1.815 µm. These figures describe an assumed pair of rigid, regular hexagonal sections. Receiving actual parts to those dimensions requires gauging.

## Geometry

For aligned socket and tool widths `S` and `f`, the allowed tool-center positions form another regular hexagon. Its apothem is `(S − f)/2` and its circumradius is `(S − f)/√3`. With a center tolerance `ρ` and eccentricity `e`, centering in the widest socket requires `f ≥ S_max − √3(ρ − e)`.

The smallest socket controls entry. For clock angle `ψ` between 0° and 30°, the rotated tool's furthest vertex projects `f(cos ψ + sin ψ/√3)/2` onto a socket face normal. At tilt `θ`, the axis can move laterally by `L tan θ` over axial reach `L`. The finite-section allowance adds two bounds based on the tool circumradius `f/√3`. Oblique projection increases the radius by at most a factor of `sec θ − 1`. The axial displacement of a tilted corner adds at most `sin θ tan θ` times the radius. The following sufficient entry inequality includes those allowances.

```text
f [(cos ψ + sin ψ/√3)/2 + (sec θ − 1 + sin θ tan θ)/√3]
  + e + L tan θ ≤ S_min/2
```

The benchmark checks face support independently by projecting six tool vertices onto six socket normals. Setting tilt, clocking and eccentricity to zero recovers the aligned-hexagon solution. The model covers dimensional fit in the fully engaged section. Torque capacity, wear and friction involve additional loads and material properties.

```sh
python3 examples/hex_drive_fit.py
python3 -m unittest benchmarks.test_hex_drive_fit
```
