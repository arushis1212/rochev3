import unittest
import numpy as np
from examples.section_calibration import fit


class SectionCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.p = np.array([[.35,.03],[.02,.31]])
        self.c = np.array([[.43,.14],[.14,.32]])

    def test_recovers_full_matrix_and_holdout(self):
        data = fit(self.p, self.c @ self.p, .0001, .0001)
        np.testing.assert_allclose(data.measured, self.c)
        self.assertTrue(data.positive_definite_within_bound)
        p = [.12,.18]
        self.assertTrue(data.check(p, self.c @ p, .0001, .0001)["within_bound"])
        self.assertFalse(data.check(p, self.c @ p + .02, .0001, .0001)["within_bound"])

    def test_entrywise_worst_corner_perturbations(self):
        from itertools import product
        for bits in product((-1.,1.), repeat=8):
            dp = .001 * np.array(bits[:4]).reshape(2,2)
            dy = .002 * np.array(bits[4:]).reshape(2,2)
            result = fit(self.p + dp, self.c @ self.p + dy, .001, .002)
            self.assertLessEqual(np.linalg.norm(result.measured-self.c, 2), result.error_bound)
            self.assertLessEqual(np.linalg.norm(result.symmetric-self.c, 2), result.error_bound)

    def test_uncertain_force_rank(self):
        with self.assertRaises(ValueError):
            fit([[.1,.1],[0,.0001]],self.c,.0001,.001)

    def test_nonreciprocity_and_uncertain_stiffness(self):
        data=fit(np.eye(2), [[.7,.5],[.1,.4]], .001,.001)
        self.assertFalse(data.reciprocity_within_bound)
        self.assertFalse(data.positive_definite_within_bound)
        data=fit(np.eye(2), [[.01,0],[0,.01]], .001,.1)
        self.assertFalse(data.positive_definite_within_bound)

    def test_rejects_bad_values(self):
        for err in (-.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                fit(self.p,self.c,err,.001)
        with self.assertRaises(ValueError):
            fit(self.p,[[.4,.2]],0,0)
