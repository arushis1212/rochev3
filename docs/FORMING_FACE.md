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

The working yarn and deforming brass were simulated together from 305.500 to 309.500 µs. Across 160 successive 25 ns intervals, the normal force reaches 16.302 mN at the 88th midpoint and 33.235 mN at the 160th. The nominal model assumes zero tangential friction on brass. The trace gives each midpoint force alongside the kinetic energy, strain energy and accumulated external work at the end of that interval. The stored elastic history carries across the change from 54 to 264 surface displacement coordinates. [Download the force and energy trace](../examples/forming_face/forming_pulse.csv)

At an assumed brass sliding coefficient of 0.20, two independent simulations give 16.431678 mN and 16.431711 mN at the same 307.700 µs endpoint, using 25 ns and 12.5 ns steps. These results describe the beginning of loading in the nominal setup. A yarn lot and brass finish can be tested at the actual contact load and speed to determine their sliding coefficient.

Run `python3 -m unittest benchmarks.test_forming_pulse` to check the timing, force samples and energy balance of the 160 intervals.
