import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from physics.bounded_dense_quadratic import minimize_spd_box_bvls
from physics.boxed_quadratic import minimize_spd_box


class BoundedDenseQuadraticTests(unittest.TestCase):
    def test_matches_independent_exhaustive_small_faces(self):
        rng = np.random.default_rng(30917)
        for n in (1, 2, 5, 7):
            for _ in range(4):
                A = rng.normal(size=(n, n)); H = A.T@A + .5*np.eye(n)
                g = rng.normal(size=n); limit = .3
                expected, _ = minimize_spd_box(H, g, limit)
                actual, report = minimize_spd_box_bvls(H, g, limit)
                np.testing.assert_allclose(actual, expected, atol=2e-10, rtol=2e-10)
                self.assertLessEqual(report['kkt_scaled_residual'], 1e-10)

    def test_dense_nineteen_known_active_kkt_solutions(self):
        rng = np.random.default_rng(9071)
        for phase in range(3):
            n = 19; limit = .003
            A = rng.normal(size=(n, n)); H = A.T@A + .25*np.eye(n)
            status = (np.arange(n)+phase)%3-1
            expected = np.where(status == 0, rng.uniform(-.002, .002, n), status*limit)
            qgradient = np.where(status == 0, 0., -status*rng.uniform(.01, .2, n))
            g = qgradient-H@expected
            actual, report = minimize_spd_box_bvls(H, g, limit)
            np.testing.assert_allclose(actual, expected, atol=2e-12, rtol=2e-10)
            self.assertLessEqual(report['kkt_residual_N'], 1e-10)

    def test_bad_domains_and_nonfinite_intermediates(self):
        for H, g, limit in [(np.eye(20),np.ones(20),1.),
                (np.diag([1.,-1.]),np.ones(2),1.),
                (np.array([[1.,1e-14],[0.,1.]]),np.ones(2),1.),
                (np.eye(2),np.ones(2),True),
                (np.eye(2)*1e308,np.ones(2),1e308),
                (np.eye(2),np.array([np.inf,1.]),1.)]:
            with self.assertRaises(ValueError):minimize_spd_box_bvls(H,g,limit)

    def test_false_success_flag_cannot_replace_kkt(self):
        result = SimpleNamespace(x=np.zeros(2),active_mask=np.zeros(2),status=1,nit=1)
        with patch('physics.bounded_dense_quadratic.lsq_linear',return_value=result):
            with self.assertRaisesRegex(ValueError,'KKT'):
                minimize_spd_box_bvls(np.eye(2),np.ones(2),.1)

    def test_inputs_remain_unchanged_and_bound_status_is_checked(self):
        H=np.eye(2);g=np.array([1.,-2.]);H.setflags(write=False);g.setflags(write=False)
        d,_=minimize_spd_box_bvls(H,g,.1)
        np.testing.assert_array_equal(d,[-.1,.1]);np.testing.assert_array_equal(g,[1.,-2.])
        result=SimpleNamespace(x=np.zeros(2),active_mask=np.ones(2),status=1,nit=1)
        with patch('physics.bounded_dense_quadratic.lsq_linear',return_value=result):
            with self.assertRaisesRegex(ValueError,'active bound'):
                minimize_spd_box_bvls(H,g,.1)


if __name__=='__main__':unittest.main()
