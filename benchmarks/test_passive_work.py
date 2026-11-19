import unittest
from fractions import Fraction

from examples.passive_work import Interval, passive_budget


class PassiveWorkTests(unittest.TestCase):
    exact = staticmethod(Interval.exact)

    def test_intermediate_shortfall_before_balanced_endpoint(self):
        q = self.exact
        report = passive_budget([(q(4), q(3)), (q(-5), q(1)), (q(1), q(0))])
        self.assertEqual([p.low for p in report.available], [0, 1, -2, 0])
        self.assertEqual(report.required_extra, q(2))
        self.assertEqual(report.outcome, "deficit")

    def test_initial_energy_covers_shortfall(self):
        q = self.exact
        report = passive_budget([(q(-2), q(0))], q(2))
        self.assertEqual(report.outcome, "within available energy")

    def test_released_elastic_energy_can_fund_extracted_work(self):
        q = self.exact
        self.assertEqual(passive_budget([(q(-3), q(-5))]).available[-1], q(2))

    def test_uncertain_budget(self):
        report = passive_budget([(Interval(-2, 2), self.exact(1))])
        self.assertEqual(report.outcome, "uncertain")
        self.assertEqual(report.required_extra, Interval(0, 3))

    def test_fractional_units_and_empty_command(self):
        q = self.exact
        self.assertEqual(passive_budget([]).required_extra, q(0))
        value = Fraction(1, 1000000)
        report = passive_budget([(q(0), q(value))])
        self.assertEqual(report.required_extra, q(value))

    def test_invalid_intervals(self):
        with self.assertRaises(ValueError):
            Interval(2, 1)
        with self.assertRaises(ValueError):
            passive_budget([], Interval(-1, 3))
