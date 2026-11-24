import json
import unittest
from pathlib import Path

import numpy as np

from examples.forming_face.forming_face import closest_gap, crossing


DATA = json.loads((Path(__file__).resolve().parents[1] / "examples/forming_face/working_edge.json").read_text())


class FormingFaceTest(unittest.TestCase):
    def test_planar_face_and_finite_yarn_endpoint(self):
        plane = dict(DATA, face_start_u_mm=0., face_span_mm=1., high_v_mm=0., drop_mm=0.)
        gap, fraction, _ = closest_gap(plane, [[-.2,-.5,0],[-.1,-.5,0]])
        self.assertAlmostEqual(gap, np.hypot(.1,.5)-.3)
        self.assertAlmostEqual(fraction, 1.)

    def test_native_solid_reference(self):
        for path, reference in zip(DATA["paths"], (305.573414941,305.573868557)):
            time, fraction, point = crossing(DATA, path)
            self.assertLess(abs(time-reference), 2e-6)
            self.assertAlmostEqual(fraction, .904752, places=5)
            np.testing.assert_allclose(point,[1.699594,1.583647,.154379],rtol=0,atol=2e-6)
