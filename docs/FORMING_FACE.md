# When the working yarn reaches the forming face

In two simulated approaches the moving yarn first reaches the nominal brass gate at **305.573415 µs** and **305.573869 µs**. The point of contact is about 90.48% along the finite yarn segment. The separately computed solid-model location is U = 1.699594 mm, V = 1.583647 mm and W = 0.154379 mm in the gate's local frame.

Run the example from the repository root with NumPy installed.

```sh
python3 examples/forming_face/forming_face.py
python3 -m unittest benchmarks.test_forming_face
```

The dataset contains both endpoints of a 0.600 mm diameter yarn segment, its velocity and its acceleration over two independently calculated incoming time steps. The 0.400 mm long face has a cubic height profile with a 0.130 mm drop. For each trial time the example minimizes the distance from the finite segment to that profile and checks the face width. Contact occurs when the minimum centerline distance reaches the yarn radius. The benchmark cross-checks the result against the native solid and includes an analytical test where the closest point lies at the end of the yarn segment.

The reported times describe one simulated setup with the nominal gate setting. Physical timing depends on the installed position and the yarn under load. [Gate assembly and dimensions](P5_MOUNTING.md)
