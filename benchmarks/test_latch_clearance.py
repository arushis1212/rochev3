"""Independent native checks of the shoulder relief and the original registered yarn."""
import importlib.util
import json
import unittest

import numpy as np

from examples.indexed_latch import ASSETS, release_events, yarn_clearance


@unittest.skipUnless(importlib.util.find_spec("cadquery"), "Native STEP checks require CadQuery")
class LatchClearance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import cadquery as cq
        cls.cq = cq
        cls.directory = ASSETS / "relieved"
        cls.spec = json.loads((cls.directory / "spec.json").read_text())
        cls.frame = json.loads((ASSETS / "interface.json").read_text())
        cls.origin, cls.axis, cls.normal = [np.asarray(cls.frame[key]) for key in
                                          ("origin_mm", "slide_axis", "swivel_axis")]
        cls.parts = {}
        for key in ("relieved_fork", "relieved_rotor", "shallow_fork_envelope", "deep_removal_envelope"):
            cls.parts[key] = cq.importers.importStep(str(cls.directory / (key + ".step"))).val()
        with np.load(ASSETS / "reference_yarn.npz") as sample:
            cls.xyz = sample["positions_mm"]
            cls.material = sample["material_mm"]

    def test_axis_sweep_and_position_allowance(self):
        stroke = -self.frame["slide_stroke_mm"] * self.axis
        radius = self.frame["reference_yarn_radius_mm"]
        def clearance(part):
            return yarn_clearance(part, stroke, self.xyz, radius, cap=.115)
        nominal = clearance(self.parts["relieved_fork"])
        machinable = clearance(self.parts["shallow_fork_envelope"])
        root = self.parts["relieved_rotor"].rotate(tuple(self.origin), tuple(self.origin + self.normal), -90)
        self.assertAlmostEqual(nominal, .044651943, places=7)
        self.assertAlmostEqual(machinable, .040953975, places=7)
        self.assertGreater(clearance(root), .1075)
        allowance = sum(self.spec["total_allowed_withdrawal_perturbations_mm"].values())
        self.assertGreater(machinable - allowance, .00595)
        events = release_events(self.frame, self.xyz, self.material)
        self.assertEqual([s["loop"] for s in events], ["L1", "L0"])
        np.testing.assert_allclose([s["stroke_mm"] for s in events], [3.774357, 23.853044], atol=1e-6)

    def test_preserved_material_bearing(self):
        fork = self.parts["relieved_fork"]
        radius = self.frame["reference_yarn_radius_mm"]
        for item in self.spec["bearing_samples"]:
            a, b = [self.cq.Vector(*v) for v in item["edge_on_fork_frame_world_axes_mm"]]
            edge = self.cq.Edge.makeLine(a, b)
            self.assertLess(abs(fork.distance(edge) - radius), .00003)
            self.assertGreater(self.parts["deep_removal_envelope"].distance(edge) - radius, .0006)

    def test_assembled_mass_and_keyed_hub(self):
        brake = json.loads((ASSETS / "brake" / "configuration.json").read_text())
        masses, centers, original = [], [], {}
        for item in brake["parts"]:
            name = item["name"]
            if name in ("fork", "rotor"):
                shape = self.parts["relieved_" + name]
            else:
                shape = self.cq.importers.importStep(str(ASSETS / item["file"])).val()
            masses.append(shape.Volume() * item["density_kg_mm3"])
            centers.append(shape.Center().toTuple())
            original[name] = shape
        self.assertAlmostEqual(sum(masses), self.spec["nominal_moving_target_kg"], places=10)
        off = np.average(centers, weights=masses, axis=0) - brake["axis_point_mm"]
        self.assertLess(np.linalg.norm(off - (off @ self.axis) * self.axis), 1.e-7)
        dog = original["index_dog"]
        for angle in [0., -90.]:
            def hub(extra):
                return original["rotor"].rotate(tuple(self.origin), tuple(self.origin + self.normal), angle + extra)
            def overlap(extra):
                return sum(s.Volume() for s in hub(extra).intersect(dog).Solids())
            self.assertLess(overlap(0.), 1e-9)
            self.assertGreater(min(overlap(-.02), overlap(.02)), 1e-5)
            self.assertGreater(hub(0.).distance(dog.translate(tuple(.470 * self.normal))), .045)


if __name__ == "__main__":
    unittest.main()
