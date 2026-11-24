# When the working yarn reaches the forming face

In two simulated approaches the moving yarn first reaches the nominal brass gate at **305.573415 µs** and **305.573869 µs**. The point of contact is about 90.48% along the finite yarn segment. The separately computed solid-model location is U = 1.699594 mm, V = 1.583647 mm and W = 0.154379 mm in the gate's local frame.

Run the example from the repository root with NumPy installed.

```sh
python3 examples/forming_face/forming_face.py
python3 -m unittest benchmarks.test_forming_face
```

The dataset contains both endpoints of a 0.600 mm diameter yarn segment, its velocity and its acceleration over two independently calculated incoming time steps. The 0.400 mm long face has a cubic height profile with a 0.130 mm drop. For each trial time the example minimizes the distance from the finite segment to that profile and checks the face width. Contact occurs when the minimum centerline distance reaches the yarn radius. The benchmark cross-checks the result against the native solid and includes an analytical test where the closest point lies at the end of the yarn segment.

The reported times describe one simulated setup with the nominal gate setting. Physical timing depends on the installed position and the yarn under load. [Gate assembly and dimensions](P5_MOUNTING.md)

## The first load pulse

The [numeric trace](../examples/forming_face/forming_pulse.csv) follows the working yarn and deforming brass together for 2.2 µs in the nominal setup, with zero assumed tangential friction on brass. Normal force grows from zero to 16.302 mN at the last midpoint. Each row gives the cell end time, its midpoint normal load, and the brass kinetic and strain energy at the end. The cumulative work can be compared directly to the sum of those energies. The full brass replay uses 23,688 displacement coordinates.

A separate coupled simulation with an assumed sliding coefficient of 0.20 checks the effect of shear and yarn spin. At 305.800 µs, independent 25 ns and 12.5 ns calculations give 0.60477246 mN and 0.60477162 mN of instantaneous normal force, respectively. The coefficient is a sensitivity input for this yarn and finish.

Run `python3 -m unittest benchmarks.test_forming_pulse` to check the 88 time intervals and the energy balance in the published trace.
