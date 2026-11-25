# Stock-tube stop for the spring shoe

A 0.500 mm steel sphere at the end of a short stainless tube provides a fixed datum for the spring shoe. The sphere contacts the underside of the steel tab. Its center stays at the same working point as the earlier indexed cup. The cartridge inserts into the jaw with the ball leading.

| Manufacturing dimension | Nominal |
|---|---:|
| Stainless stem | 24G regular-wall 304, 0.5588 mm OD × 0.3048 mm ID |
| Stem length | 0.879 mm |
| Ball center to tube front, along its axis | 0.221 mm |
| Backfill end, measured from ball center | 0.325 mm |
| Receiving bore | Ø0.750 mm, 118° drill point |
| Bore direction in clamp coordinates | (−0.8365163, +0.5000000, +0.2241439) |
| Installed ball center XYZ | (11.7000, −2.0994, −1.7200) mm |

Import the three STEP files into one assembly using their native coordinates. The ball center is the local origin and +Y runs into the tube. The backfill occupies the spherical cap inside the tube and leaves its working hemisphere exposed. [Ball](BALL_LOCAL.step) · [Tube](TUBE_LOCAL.step) · [Bond shape](BOND_LOCAL.step)

Cut and deburr the stainless stock while supported. Hold the tube and sphere coaxially during bonding, keep the working surface clean, and measure the tip projection after cure. At assembly, set the ball against a calibrated spring-shoe reference before curing the outer support land. The catalog lists the 304H24RW range as 0.5588–0.5715 mm OD and 0.2921–0.3302 mm ID. [Manufacturer’s stock table](https://www.microgroup.com/products/metal-stock-custom-tubing/hypodermic-tubing/)

A full-size clearance cylinder around the inserting cartridge clears the modeled detached jaw by 0.04805 mm. The installed steel stem clears the spring tab by 0.17090 mm at the reference pose. Across a separate 80 µs, 957-edge yarn trajectory, the yarn clears the changed solid regions by at least 0.10087 mm. These checks address this interface at the stated poses and material conditions. [Feeder and gate calculations](../../docs/YARN_HANDOFF_FIXTURES.md)

## Force and displacement

The included model predicts how far the ball moves along the jaw's Y axis under a specified axial load. It uses 48 elastic modes of the steel tube, cured cap, outer adhesive land, printed jaw and ball. Its reference boundary holds the coupon faces 2.5 mm from the center in each Cartesian direction wherever the cut intersects the jaw. The bonded contact faces and the force direction come from the installed CAD. The 23°C and 40°C calculations use individual material cases with different adhesive and printed-jaw stiffnesses.

From the repository root, run the following command with Python 3.

```sh
python3 cad/feeder_cartridge/response.py --force-mn 10 --frequency-hz 0 --temperature-c 23
```

The program reports axial displacement in micrometres and accepts excitation frequencies from 0 to 18 kHz. Its static and three harmonic reference results per material case come from separate solutions of the full linear finite-element equations. A 10 mN static load gives about 0.129 µm in the room-temperature case and 0.562 µm in the warm case. These values describe elastic displacement of the bonded cartridge relative to the local jaw fixture. [Mode data](AXIAL_MODES.json) · [Calculation](response.py)
