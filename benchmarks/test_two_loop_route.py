import unittest
from examples.two_loop_route import measure


class FiniteToolRouteTests(unittest.TestCase):
    def test_route_enters_both_registered_disks(self):
        r=measure()
        self.assertEqual(r['translation_legs'],7)
        self.assertEqual([(e['loop'], e['sign']) for e in r['crossings']], [('L1',1),('L0',1)])
